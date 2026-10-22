import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.policies import delete_documents, get_document_hashes, replace_document
from app.embeddings import EmbeddingError, embed_documents
from app.ingest.chunking import build_chunks, content_hash

logger = logging.getLogger(__name__)

_sleep = asyncio.sleep  # replaced in tests so they do not wait


@dataclass
class IngestReport:
    loaded: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)


class _Pacer:
    """Keeps embedding requests under the per-minute limit."""

    def __init__(self, requests_per_minute: int):
        self.min_gap = 60.0 / requests_per_minute
        self.last_call: float | None = None

    async def wait(self) -> None:
        if self.last_call is not None:
            remaining = self.min_gap - (time.monotonic() - self.last_call)
            if remaining > 0:
                await _sleep(remaining)
        self.last_call = time.monotonic()


async def ingest_policies(session: AsyncSession, policies_dir: Path | None = None) -> IngestReport:
    policies_dir = Path(policies_dir or settings.policies_dir)
    if not policies_dir.is_dir():
        # Never treat a wrong path as "all files deleted".
        raise FileNotFoundError(f"Policies folder not found: {policies_dir}")

    report = IngestReport()
    stored_hashes = await get_document_hashes(session)
    pacer = _Pacer(settings.embedding_requests_per_minute)
    files = sorted(policies_dir.glob("*.md"))

    for path in files:
        text = path.read_text(encoding="utf-8")
        file_hash = content_hash(text)
        if stored_hashes.get(path.name) == file_hash:
            report.skipped.append(path.name)
            continue

        try:
            title, chunks = build_chunks(text, settings.max_chunk_chars)
        except ValueError as exc:
            report.failed[path.name] = str(exc)
            continue
        if not chunks:
            report.failed[path.name] = "no '##' sections with text"
            continue

        # All embeddings are created BEFORE the transaction opens, so it stays short.
        try:
            await pacer.wait()
            vectors = await embed_documents([(title, chunk.text) for chunk in chunks])
        except EmbeddingError as exc:
            report.failed[path.name] = f"embedding failed: {exc}"
            continue

        try:
            await replace_document(
                session,
                source_file=path.name,
                title=title,
                content_hash=file_hash,
                chunks=[
                    {"section": chunk.section, "chunk_text": chunk.text, "embedding": vector}
                    for chunk, vector in zip(chunks, vectors)
                ],
            )
        except Exception:
            logger.exception("Saving %s failed", path.name)
            report.failed[path.name] = "database error (old chunks kept)"
            continue
        report.loaded.append(path.name)

    current_files = {path.name for path in files}
    gone = sorted(name for name in stored_hashes if name not in current_files)
    if gone:
        await delete_documents(session, gone)
        report.removed = gone

    return report
