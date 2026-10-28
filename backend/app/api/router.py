from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.history import router as history_router
from app.api.orders import router as orders_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(admin_router)
router.include_router(chat_router, tags=["chat"])
router.include_router(history_router, tags=["history"])
router.include_router(orders_router, tags=["orders"])
