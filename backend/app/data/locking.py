from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text

from app.data.database import engine


@asynccontextmanager
async def customer_lock(customer_id: str) -> AsyncIterator[None]:
    # Dedicated connection: the session's connection goes back to the pool on every
    # commit, which would leave a session-level advisory lock held forever.
    async with engine.connect() as conn:
        await conn.execute(text("SELECT pg_advisory_lock(hashtext(:cid))"), {"cid": customer_id})
        try:
            yield
        finally:
            await conn.execute(text("SELECT pg_advisory_unlock(hashtext(:cid))"), {"cid": customer_id})
