"""Tests for demo stock reset: data layer + admin endpoint."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Product, SystemSetting
from app.data.products import (
    STOCK_RESET_KEY,
    check_and_reset_daily_stock,
    reset_all_stock,
)


# ── Data layer ──


class TestResetAllStock:
    async def test_resets_changed_stock_to_default(self, seeded_session):
        session = seeded_session
        await session.execute(
            update(Product).where(Product.id == "PHN001").values(stock=0)
        )
        await session.execute(
            update(Product).where(Product.id == "LAP001").values(stock=2)
        )
        await session.commit()

        count = await reset_all_stock(session)
        assert count == 2

        row1 = (await session.execute(select(Product).where(Product.id == "PHN001"))).scalar_one()
        assert row1.stock == row1.default_stock
        row2 = (await session.execute(select(Product).where(Product.id == "LAP001"))).scalar_one()
        assert row2.stock == row2.default_stock

    async def test_returns_zero_when_nothing_changed(self, seeded_session):
        count = await reset_all_stock(seeded_session)
        assert count == 0


class TestCheckAndResetDailyStock:
    async def _clear_setting(self, session):
        row = (await session.execute(
            select(SystemSetting).where(SystemSetting.key == STOCK_RESET_KEY)
        )).scalar_one_or_none()
        if row:
            await session.delete(row)
            await session.commit()

    async def test_resets_on_first_call_of_day(self, seeded_session):
        session = seeded_session
        await self._clear_setting(session)
        await session.execute(
            update(Product).where(Product.id == "PHN001").values(stock=0)
        )
        await session.commit()

        result = await check_and_reset_daily_stock(session)
        assert result is True

        row = (await session.execute(select(Product).where(Product.id == "PHN001"))).scalar_one()
        assert row.stock == row.default_stock

        setting = (await session.execute(
            select(SystemSetting).where(SystemSetting.key == STOCK_RESET_KEY)
        )).scalar_one()
        assert setting.value == date.today().isoformat()

    async def test_skips_if_already_reset_today(self, seeded_session):
        session = seeded_session
        await self._clear_setting(session)
        await check_and_reset_daily_stock(session)

        result = await check_and_reset_daily_stock(session)
        assert result is False

    async def test_resets_after_date_changes(self, seeded_session):
        session = seeded_session
        await self._clear_setting(session)
        await check_and_reset_daily_stock(session)

        yesterday = (date.today() - timedelta(days=1)).isoformat()
        row = (await session.execute(
            select(SystemSetting).where(SystemSetting.key == STOCK_RESET_KEY)
        )).scalar_one()
        row.value = yesterday
        await session.commit()

        await session.execute(
            update(Product).where(Product.id == "PHN002").values(stock=0)
        )
        await session.commit()

        result = await check_and_reset_daily_stock(session)
        assert result is True

        p = (await session.execute(select(Product).where(Product.id == "PHN002"))).scalar_one()
        assert p.stock == p.default_stock


# ── Admin endpoint ──


class TestAdminStockReset:
    @pytest.fixture
    async def client(self, engine, setup_db):
        from fastapi.testclient import TestClient
        from app.main import app
        from app.data.database import get_db

        async with engine.connect() as conn:
            trans = await conn.begin()
            async_session = AsyncSession(
                bind=conn, join_transaction_mode="rollback_only", expire_on_commit=False,
            )

            async def override_get_db():
                yield async_session

            app.dependency_overrides[get_db] = override_get_db
            with TestClient(app) as c:
                yield c
            app.dependency_overrides.clear()
            await async_session.close()
            await trans.rollback()

    def _admin_auth(self, client) -> dict:
        resp = client.post("/admin/login", json={
            "username": "testadmin", "password": "testpass123",
        })
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def test_stock_reset_requires_admin(self, client):
        resp = client.post("/admin/stock-reset")
        assert resp.status_code == 401

    @patch("app.api.admin.reset_all_stock", new_callable=AsyncMock, return_value=5)
    def test_stock_reset_returns_count(self, mock_reset, client):
        headers = self._admin_auth(client)
        resp = client.post("/admin/stock-reset", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["products_reset"] == 5
