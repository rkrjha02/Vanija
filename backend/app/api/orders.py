from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.buttons import confirm_cancel, confirm_order
from app.auth.dependencies import get_current_customer
from app.data.customers import get_customer
from app.data.database import get_db
from app.data.locking import customer_lock

router = APIRouter()


class ConfirmOrderRequest(BaseModel):
    pending_id: int
    save_address: bool = False


class ConfirmCancelRequest(BaseModel):
    order_id: int


async def _require_customer(session: AsyncSession, customer_id: str) -> None:
    if not await get_customer(session, customer_id):
        raise HTTPException(status_code=404, detail="Customer not found")


@router.post("/orders/confirm")
async def confirm_order_endpoint(
    req: ConfirmOrderRequest,
    current: dict = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db),
):
    customer_id = current["customer_id"]
    await _require_customer(session, customer_id)
    async with customer_lock(customer_id):
        return await confirm_order(session, customer_id, req.pending_id, req.save_address)


@router.post("/orders/cancel")
async def confirm_cancel_endpoint(
    req: ConfirmCancelRequest,
    current: dict = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db),
):
    customer_id = current["customer_id"]
    await _require_customer(session, customer_id)
    async with customer_lock(customer_id):
        return await confirm_cancel(session, customer_id, req.order_id)
