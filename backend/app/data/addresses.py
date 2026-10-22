from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Address

ADDRESS_FIELDS = ("recipient_name", "phone", "address_line", "city", "state", "pincode")


def _address_to_dict(a: Address) -> dict:
    return {
        "id": a.id,
        "recipient_name": a.recipient_name,
        "phone": a.phone,
        "address_line": a.address_line,
        "city": a.city,
        "state": a.state,
        "pincode": a.pincode,
        "is_default": a.is_default,
    }


async def list_addresses(session: AsyncSession, customer_id: str) -> list[dict]:
    result = await session.execute(
        select(Address)
        .where(Address.customer_id == customer_id)
        .order_by(Address.is_default.desc(), Address.id)
    )
    return [_address_to_dict(a) for a in result.scalars().all()]


async def get_address_for_customer(
    session: AsyncSession, address_id: int, customer_id: str
) -> dict | None:
    result = await session.execute(
        select(Address).where(
            Address.id == address_id,
            Address.customer_id == customer_id,
        )
    )
    address = result.scalars().first()
    return _address_to_dict(address) if address else None


async def save_address(session: AsyncSession, customer_id: str, fields: dict) -> int:
    has_any = select(Address.id).where(Address.customer_id == customer_id).exists()
    result = await session.execute(
        insert(Address)
        .values(
            customer_id=customer_id,
            is_default=~has_any,
            **{name: fields[name] for name in ADDRESS_FIELDS},
        )
        .returning(Address.id)
    )
    address_id = result.scalar_one()
    await session.commit()
    return address_id
