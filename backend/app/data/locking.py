import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text

from app.config import settings
from app.data.database import engine

POLL_INTERVAL = 0.5


class LockTimeoutError(Exception):
    pass


@asynccontextmanager
async def customer_lock(customer_id: str, timeout: float | None = None) -> AsyncIterator[None]:
    if timeout is None:
        timeout = settings.lock_wait_seconds

    async with engine.connect() as conn:
        elapsed = 0.0
        while True:
            row = await conn.execute(
                text("SELECT pg_try_advisory_lock(hashtext(:cid))"),
                {"cid": customer_id},
            )
            acquired = row.scalar()
            if acquired:
                break
            elapsed += POLL_INTERVAL
            if elapsed > timeout:
                raise LockTimeoutError(
                    f"Could not acquire lock for customer within {timeout}s"
                )
            await asyncio.sleep(POLL_INTERVAL)

        try:
            yield
        finally:
            await conn.execute(
                text("SELECT pg_advisory_unlock(hashtext(:cid))"),
                {"cid": customer_id},
            )
