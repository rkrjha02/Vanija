from sqlalchemy import delete, func, insert, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import PolicyChunk, PolicyDocument


async def get_document_hashes(session: AsyncSession) -> dict[str, str]:
    """Return {source_file: content_hash} for every stored policy document."""
    result = await session.execute(
        select(PolicyDocument.source_file, PolicyDocument.content_hash)
    )
    return {row.source_file: row.content_hash for row in result}


async def replace_document(
    session: AsyncSession,
    source_file: str,
    title: str,
    content_hash: str,
    chunks: list[dict],
) -> int:
    """Store a document and replace all its chunks in ONE transaction.

    Each chunk dict has: section, chunk_text, embedding.
    If anything fails, nothing changes (the old chunks stay).
    """
    try:
        stmt = pg_insert(PolicyDocument).values(
            source_file=source_file, title=title, content_hash=content_hash
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[PolicyDocument.source_file],
            set_={"title": title, "content_hash": content_hash, "updated_at": func.now()},
        ).returning(PolicyDocument.id)
        document_id = (await session.execute(stmt)).scalar_one()

        await session.execute(
            delete(PolicyChunk).where(PolicyChunk.document_id == document_id)
        )
        if chunks:
            await session.execute(
                insert(PolicyChunk),
                [
                    {
                        "document_id": document_id,
                        "chunk_index": index,
                        "section": chunk["section"],
                        "chunk_text": chunk["chunk_text"],
                        "embedding": chunk["embedding"],
                    }
                    for index, chunk in enumerate(chunks)
                ],
            )
    except Exception:
        await session.rollback()
        raise
    await session.commit()
    return document_id


async def delete_documents(session: AsyncSession, source_files: list[str]) -> int:
    """Delete documents (their chunks go with them). Returns how many were deleted."""
    if not source_files:
        return 0
    result = await session.execute(
        delete(PolicyDocument).where(PolicyDocument.source_file.in_(source_files))
    )
    await session.commit()
    return result.rowcount


async def get_chunks(session: AsyncSession, source_file: str) -> list[dict]:
    """Return a document's chunks in order (section and text only)."""
    result = await session.execute(
        select(PolicyChunk.section, PolicyChunk.chunk_text)
        .join(PolicyDocument, PolicyChunk.document_id == PolicyDocument.id)
        .where(PolicyDocument.source_file == source_file)
        .order_by(PolicyChunk.chunk_index)
    )
    return [{"section": row.section, "chunk_text": row.chunk_text} for row in result]


async def search_chunks(
    session: AsyncSession,
    vector: list[float],
    limit: int,
    min_similarity: float,
) -> list[dict]:
    """Return up to `limit` chunks closest to `vector`, best first.

    Similarity = 1 - cosine distance (1 means the same direction).
    Chunks below `min_similarity` are dropped.
    """
    distance = PolicyChunk.embedding.cosine_distance(vector)
    result = await session.execute(
        select(
            PolicyDocument.title,
            PolicyDocument.source_file,
            PolicyChunk.section,
            PolicyChunk.chunk_text,
            (1 - distance).label("similarity"),
        )
        .join(PolicyDocument, PolicyChunk.document_id == PolicyDocument.id)
        .where(distance <= 1 - min_similarity)
        .order_by(distance)
        .limit(limit)
    )
    chunks = []
    for row in result:
        prefix = f"{row.title} > {row.section}: "
        text = row.chunk_text[len(prefix):] if row.chunk_text.startswith(prefix) else row.chunk_text
        chunks.append({
            "document_title": row.title,
            "source_file": row.source_file,
            "section": row.section,
            "text": text,
            "similarity": float(row.similarity),
        })
    return chunks
