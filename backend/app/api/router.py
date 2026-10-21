from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.customers import router as customers_router

router = APIRouter()
router.include_router(customers_router, tags=["customers"])
router.include_router(chat_router, tags=["chat"])
