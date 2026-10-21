import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Customer


async def create_customer(session: AsyncSession) -> str:
    customer_id = secrets.token_urlsafe(32)
    customer = Customer(id=customer_id)
    session.add(customer)
    await session.commit()
    return customer_id


async def get_customer(session: AsyncSession, customer_id: str) -> dict | None:
    result = await session.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return {"id": row.id, "phone": row.phone, "name": row.name}
