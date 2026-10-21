from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.customers import create_customer
from app.data.database import get_db

router = APIRouter()


@router.post("/customers")
async def create_new_customer(session: AsyncSession = Depends(get_db)):
    customer_id = await create_customer(session)
    return {"customer_id": customer_id}
