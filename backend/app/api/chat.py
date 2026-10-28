from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.loop import run_agent_loop
from app.auth.dependencies import get_current_customer
from app.data.customers import get_customer
from app.data.database import get_db
from app.data.locking import LockTimeoutError, customer_lock

LOCK_BUSY_REPLY = "I'm still working on your previous message. Please send your message again in a moment."

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def send_message(
    req: ChatRequest,
    current: dict = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db),
):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    customer_id = current["customer_id"]
    customer = await get_customer(session, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    try:
        async with customer_lock(customer_id):
            result = await run_agent_loop(session, customer_id, req.message.strip())
    except LockTimeoutError:
        return {"reply_text": LOCK_BUSY_REPLY, "cards": []}

    return result
