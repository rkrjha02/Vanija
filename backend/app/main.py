import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

from app.api.router import router
from app.config import settings
from app.data.database import async_session
from app.data.products import get_categories
from app.tools.definitions import VALID_CATEGORIES

LOCAL_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]


def _build_allowed_origins() -> list[str]:
    extra = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
    return LOCAL_ORIGINS + extra


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session() as session:
        categories = await get_categories(session)
        VALID_CATEGORIES.clear()
        VALID_CATEGORIES.extend(categories)
    yield


app = FastAPI(title="Electronics Sales Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
