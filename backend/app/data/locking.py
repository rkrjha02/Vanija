from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def acquire_customer_lock(session: AsyncSession, customer_id: str) -> None:
    await session.execute(
        text("SELECT pg_advisory_lock(hashtext(:cid))"),
        {"cid": customer_id},
    )
