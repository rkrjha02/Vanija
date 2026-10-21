from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.data.database import async_session
from app.data.products import get_categories
from app.tools.definitions import VALID_CATEGORIES


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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
