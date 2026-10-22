import asyncio
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.data.models import Base, Product

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEST_PRODUCTS = [
    Product(id="PHN001", name="Phone A", category="phone", brand="Samsung",
            price=9999, stock=10, description="A budget phone",
            specs={"ram_gb": 4, "battery_mah": 5000, "camera_mp": 50, "storage_gb": 128}),
    Product(id="PHN002", name="Phone B", category="phone", brand="Xiaomi",
            price=14999, stock=5, description="A mid-range phone",
            specs={"ram_gb": 6, "battery_mah": 5000, "camera_mp": 108, "storage_gb": 128}),
    Product(id="PHN003", name="Phone C", category="phone", brand="Samsung",
            price=19999, stock=0, description="Out of stock phone",
            specs={"ram_gb": 8, "battery_mah": 4500, "camera_mp": 50, "storage_gb": 256}),
    Product(id="LAP001", name="Laptop A", category="laptop", brand="HP",
            price=45999, stock=8, description="A work laptop",
            specs={"ram_gb": 16, "storage_gb": 512, "display_inch": 15.6, "processor": "Intel i5"}),
    Product(id="HPH001", name="Headphone A", category="headphone", brand="Sony",
            price=2999, stock=20, description="Wireless headphones",
            specs={"battery_hours": 30, "noise_cancelling": True, "connectivity": "Bluetooth 5.0"}),
    Product(id="PHN099", name="Inactive Phone", category="phone", brand="Test",
            price=5000, stock=10, description="This product is inactive",
            is_active=False,
            specs={"ram_gb": 2, "battery_mah": 3000, "camera_mp": 12, "storage_gb": 32}),
]


@pytest.fixture(scope="session")
def engine():
    if not settings.test_database_url:
        pytest.skip("TEST_DATABASE_URL not set")
    return create_async_engine(settings.test_database_url, pool_pre_ping=True)


@pytest.fixture(scope="session")
async def setup_db(engine):
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(engine, setup_db):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def seeded_session(session):
    for product in TEST_PRODUCTS:
        merged = await session.merge(product)
    await session.commit()
    yield session


@pytest.fixture
async def order_session(session):
    # Fresh stock and price every test, because placing orders changes them.
    await session.merge(Product(id="ORD001", name="Order Phone", category="phone", brand="X",
                                price=1000, stock=5, description="", is_active=True, specs={}))
    await session.merge(Product(id="ORD002", name="Order Laptop", category="laptop", brand="Y",
                                price=30000, stock=3, description="", is_active=True, specs={}))
    await session.commit()
    yield session
