"""Embed product data for semantic search.

Run from backend/:  python -m app.ingest_products
"""

import asyncio
import sys

from app.data.database import async_session, engine
from app.ingest.product_embeddings import embed_products


async def main() -> int:
    print("Embedding products...")
    async with async_session() as session:
        report = await embed_products(session)
    await engine.dispose()

    if report.failed:
        print(f"  FAILED: {', '.join(report.failed)}")
    print(
        f"Done: {report.embedded} embedded, {report.skipped} skipped (unchanged)"
        f"{f', {len(report.failed)} failed' if report.failed else ''}."
    )
    return 1 if report.failed else 0


if __name__ == "__main__":
    kwargs = {}
    if sys.platform == "win32":
        kwargs["loop_factory"] = asyncio.SelectorEventLoop
    sys.exit(asyncio.run(main(), **kwargs))
