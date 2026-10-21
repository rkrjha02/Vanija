from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.conversations import get_or_create_conversation
from app.data.customers import get_customer
from app.data.database import get_db
from app.data.messages import get_recent_messages

router = APIRouter()


@router.get("/history/{customer_id}")
async def get_history(customer_id: str, session: AsyncSession = Depends(get_db)):
    customer = await get_customer(session, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    conversation = await get_or_create_conversation(session, customer_id)
    messages = await get_recent_messages(
        session, conversation["id"], limit=settings.recent_messages_count
    )
    return {"messages": messages}
