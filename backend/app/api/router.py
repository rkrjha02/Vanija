from fastapi import APIRouter

from app.api.chat import router as chat_router
from app.api.customers import router as customers_router
from app.api.history import router as history_router

router = APIRouter()
router.include_router(customers_router, tags=["customers"])
router.include_router(chat_router, tags=["chat"])
router.include_router(history_router, tags=["history"])
