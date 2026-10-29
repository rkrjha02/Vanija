from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_customer
from app.config import settings
from app.data.conversations import get_or_create_conversation
from app.data.customers import get_customer
from app.data.database import get_db
from app.data.messages import get_history_page

router = APIRouter()


@router.get("/history")
async def get_history(
    before: int | None = Query(None, gt=0),
    current: dict = Depends(get_current_customer),
    session: AsyncSession = Depends(get_db),
):
    customer_id = current["customer_id"]
    customer = await get_customer(session, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # The conversation comes from the login token, so `before` can only page through this customer's own chat.
    conversation = await get_or_create_conversation(session, customer_id)
    return await get_history_page(
        session, conversation["id"], before_id=before, limit=settings.history_page_size
    )
