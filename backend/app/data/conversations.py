from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Conversation


async def get_or_create_conversation(
    session: AsyncSession, customer_id: str
) -> dict:
    result = await session.execute(
        select(Conversation).where(Conversation.customer_id == customer_id)
    )
    conv = result.scalar_one_or_none()

    if conv is None:
        conv = Conversation(customer_id=customer_id, shown_products=[])
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

    return {
        "id": conv.id,
        "customer_id": conv.customer_id,
        "shown_products": conv.shown_products or [],
    }


async def update_shown_products(
    session: AsyncSession, conversation_id: int, shown_products: list
) -> None:
    await session.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(shown_products=shown_products)
    )
    await session.commit()
