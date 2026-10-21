from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.loop import run_agent_loop
from app.data.customers import get_customer
from app.data.database import get_db

router = APIRouter()


class ChatRequest(BaseModel):
    customer_id: str
    message: str


@router.post("/chat")
async def send_message(req: ChatRequest, session: AsyncSession = Depends(get_db)):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    customer = await get_customer(session, req.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    result = await run_agent_loop(session, req.customer_id, req.message.strip())
    return result
