import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Customer, User


async def create_customer(session: AsyncSession) -> str:
    user_id = uuid.uuid4().hex
    user = User(id=user_id, email=f"{user_id}@placeholder.local", name="Guest")
    session.add(user)
    await session.flush()
    customer_id = uuid.uuid4().hex
    customer = Customer(id=customer_id, user_id=user_id)
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
