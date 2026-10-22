"""Tests for the ingest command. Embeddings are faked; no real API calls."""

import pytest
from sqlalchemy import delete

import app.ingest.ingest as ingest_mod
from app.config import settings
from app.data.models import PolicyDocument
from app.data.policies import get_chunks, get_document_hashes
from app.embeddings import EmbeddingError
from app.ingest.ingest import ingest_policies

DIMS = settings.embedding_dimensions

RETURNS = "# Returns Policy\n\n## Phones\nPhones: 7 days.\n\n## Laptops\nLaptops: 10 days.\n"
WARRANTY = "# Warranty Policy\n\n## Phones\nPhones: 12 months.\n"


class FakeEmbedder:
    def __init__(self):
        self.calls = 0
        self.fail = False
        self.bad_vector_at = None  # index of a chunk to give a wrong-size vector

    async def __call__(self, items):
        self.calls += 1
        if self.fail:
            raise EmbeddingError("quota exceeded")
        vectors = [[0.01 * (i + 1)] * DIMS for i in range(len(items))]
        if self.bad_vector_at is not None:
            vectors[self.bad_vector_at] = [0.1] * 3
        return vectors


@pytest.fixture
async def clean(session):
    await session.execute(delete(PolicyDocument))
    await session.commit()
    yield session
    await session.execute(delete(PolicyDocument))
    await session.commit()


@pytest.fixture
def embedder(monkeypatch):
    fake = FakeEmbedder()
    monkeypatch.setattr(ingest_mod, "embed_documents", fake)

    async def no_wait(seconds):
        return None
    monkeypatch.setattr(ingest_mod, "_sleep", no_wait)
    return fake


@pytest.fixture
def policy_dir(tmp_path):
    (tmp_path / "returns.md").write_text(RETURNS, encoding="utf-8")
    (tmp_path / "warranty.md").write_text(WARRANTY, encoding="utf-8")
    return tmp_path


async def test_first_run_loads_all_files(clean, embedder, policy_dir):
    report = await ingest_policies(clean, policy_dir)

    assert sorted(report.loaded) == ["returns.md", "warranty.md"]
    assert embedder.calls == 2
    chunks = await get_chunks(clean, "returns.md")
    assert [c["section"] for c in chunks] == ["Phones", "Laptops"]
    assert chunks[0]["chunk_text"] == "Returns Policy > Phones: Phones: 7 days."


async def test_unchanged_files_are_skipped(clean, embedder, policy_dir):
    await ingest_policies(clean, policy_dir)
    embedder.calls = 0

    report = await ingest_policies(clean, policy_dir)

    assert sorted(report.skipped) == ["returns.md", "warranty.md"]
    assert report.loaded == []
    assert embedder.calls == 0


async def test_changed_file_is_reembedded_and_old_chunks_replaced(clean, embedder, policy_dir):
    await ingest_policies(clean, policy_dir)
    embedder.calls = 0
    (policy_dir / "returns.md").write_text(
        "# Returns Policy\n\n## Headphones\nUnopened headphones: 7 days.\n", encoding="utf-8")

    report = await ingest_policies(clean, policy_dir)

    assert report.loaded == ["returns.md"]
    assert report.skipped == ["warranty.md"]
    assert embedder.calls == 1
    chunks = await get_chunks(clean, "returns.md")
    assert [c["section"] for c in chunks] == ["Headphones"]


async def test_embedding_failure_keeps_old_chunks(clean, embedder, policy_dir):
    await ingest_policies(clean, policy_dir)
    old_hashes = await get_document_hashes(clean)
    (policy_dir / "returns.md").write_text(RETURNS + "\n## Refunds\nRefund: 5 days.\n",
                                           encoding="utf-8")
    embedder.fail = True

    report = await ingest_policies(clean, policy_dir)

    assert "returns.md" in report.failed
    assert len(await get_chunks(clean, "returns.md")) == 2
    assert await get_document_hashes(clean) == old_hashes  # so the next run retries it


async def test_database_failure_halfway_rolls_back(clean, embedder, policy_dir):
    await ingest_policies(clean, policy_dir)
    old_hashes = await get_document_hashes(clean)
    (policy_dir / "returns.md").write_text(RETURNS + "\n## Refunds\nRefund: 5 days.\n",
                                           encoding="utf-8")
    # The 2nd chunk's vector has the wrong size, so the database rejects the insert
    # AFTER the old chunks were deleted in the same transaction.
    embedder.bad_vector_at = 1

    report = await ingest_policies(clean, policy_dir)

    assert "returns.md" in report.failed
    chunks = await get_chunks(clean, "returns.md")
    assert [c["section"] for c in chunks] == ["Phones", "Laptops"]
    assert await get_document_hashes(clean) == old_hashes


async def test_deleted_file_is_removed_with_its_chunks(clean, embedder, policy_dir):
    await ingest_policies(clean, policy_dir)
    (policy_dir / "warranty.md").unlink()

    report = await ingest_policies(clean, policy_dir)

    assert report.removed == ["warranty.md"]
    assert "warranty.md" not in await get_document_hashes(clean)
    assert await get_chunks(clean, "warranty.md") == []


async def test_missing_folder_raises_and_deletes_nothing(clean, embedder, policy_dir, tmp_path):
    await ingest_policies(clean, policy_dir)

    with pytest.raises(FileNotFoundError):
        await ingest_policies(clean, tmp_path / "no_such_folder")

    assert len(await get_document_hashes(clean)) == 2


async def test_file_without_title_fails_alone(clean, embedder, policy_dir):
    (policy_dir / "broken.md").write_text("## Phones\nNo title here.\n", encoding="utf-8")

    report = await ingest_policies(clean, policy_dir)

    assert "broken.md" in report.failed
    assert sorted(report.loaded) == ["returns.md", "warranty.md"]
