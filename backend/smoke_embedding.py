"""Manual check: one REAL Gemini embedding call, stored in the dev database, then rolled back.

Run: python smoke_embedding.py   (needs GEMINI_API_KEY in .env)
"""

import asyncio
import sys

from sqlalchemy import select

from app.config import settings
from app.data.database import async_session, engine
from app.data.models import PolicyChunk, PolicyDocument
from app.embeddings import EmbeddingError, embed_documents


async def main():
    text = "Smoke Test > Phones: Phones have a 12-month warranty."
    try:
        [vector] = await embed_documents([("Smoke Test", text)])
    except EmbeddingError as exc:
        print(f"Embedding failed: {exc}")
        return

    print(f"Model: {settings.embedding_model}")
    print(f"Vector length: {len(vector)}")
    print(f"First 5 numbers: {[round(x, 4) for x in vector[:5]]}")

    async with async_session() as session:
        document = PolicyDocument(title="Smoke Test", source_file="__smoke_test__.md",
                                  content_hash="smoke")
        session.add(document)
        await session.flush()
        session.add(PolicyChunk(document_id=document.id, chunk_index=0, section="Phones",
                                chunk_text=text, embedding=vector))
        await session.flush()
        stored = (await session.execute(
            select(PolicyChunk.embedding).where(PolicyChunk.document_id == document.id)
        )).scalar_one()
        print(f"Stored and read back: {len(stored)} numbers")
        await session.rollback()
        print("Rolled back (nothing kept in the database).")

    await engine.dispose()


if __name__ == "__main__":
    kwargs = {}
    if sys.platform == "win32":
        kwargs["loop_factory"] = asyncio.SelectorEventLoop
    asyncio.run(main(), **kwargs)
