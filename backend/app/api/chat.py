from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.loop import run_agent_loop
from app.auth.dependencies import get_current_customer
from app.config import settings
from app.data.customers import get_customer
from app.data.database import get_db
from app.data.locking import LockTimeoutError, customer_lock
from app.data.products import check_and_reset_daily_stock
from app.data.rate_limits import (
    check_and_increment_customer_rate,
    check_and_increment_global_daily,
)

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

    await check_and_reset_daily_stock(session)

    if len(req.message) > settings.max_message_length:
        raise HTTPException(
            status_code=400,
            detail=f"Message is too long. Please keep it under {settings.max_message_length:,} characters.",
        )

    customer_id = current["customer_id"]
    customer = await get_customer(session, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if not await check_and_increment_global_daily(
        session, max_messages=settings.global_daily_message_limit,
    ):
        return JSONResponse(
            status_code=429,
            content={
                "reply_text": "Our demo has reached its daily limit. Please try again tomorrow.",
                "cards": [],
            },
        )

    if not await check_and_increment_customer_rate(
        session, customer_id,
        max_messages=settings.customer_hourly_message_limit,
    ):
        return JSONResponse(
            status_code=429,
            content={
                "reply_text": "You've sent a lot of messages. Please wait before continuing.",
                "cards": [],
            },
        )

    try:
        async with customer_lock(customer_id):
            result = await run_agent_loop(session, customer_id, req.message.strip())
    except LockTimeoutError:
        return {"reply_text": LOCK_BUSY_REPLY, "cards": []}

    return result
