from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.buttons import confirm_cancel, confirm_order
from app.data.customers import get_customer
from app.data.database import get_db
from app.data.locking import customer_lock

router = APIRouter()


class ConfirmOrderRequest(BaseModel):
    customer_id: str
    pending_id: int
    save_address: bool = False


class ConfirmCancelRequest(BaseModel):
    customer_id: str
    order_id: int


async def _require_customer(session: AsyncSession, customer_id: str) -> None:
    if not await get_customer(session, customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")


@router.post("/orders/confirm")
async def confirm_order_endpoint(req: ConfirmOrderRequest, session: AsyncSession = Depends(get_db)):
    await _require_customer(session, req.customer_id)
    async with customer_lock(req.customer_id):
        return await confirm_order(session, req.customer_id, req.pending_id, req.save_address)


@router.post("/orders/cancel")
async def confirm_cancel_endpoint(req: ConfirmCancelRequest, session: AsyncSession = Depends(get_db)):
    await _require_customer(session, req.customer_id)
    async with customer_lock(req.customer_id):
        return await confirm_cancel(session, req.customer_id, req.order_id)
