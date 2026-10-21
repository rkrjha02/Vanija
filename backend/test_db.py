"""Quick test: connect to Neon and run SELECT 1."""

import asyncio
import selectors
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


async def main():
    engine = create_async_engine(settings.database_url, echo=True)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print(f"Result: {result.scalar()}")
    await engine.dispose()


if __name__ == "__main__":
    kwargs = {}
    if sys.platform == "win32":
        kwargs["loop_factory"] = asyncio.SelectorEventLoop
    asyncio.run(main(), **kwargs)
