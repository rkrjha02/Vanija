"""Tests for rate limiting: data layer + chat endpoint integration."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import RateLimit
from app.data.rate_limits import (
    IST,
    _latest_midnight_ist,
    check_and_increment_customer_rate,
    check_and_increment_global_daily,
)
from app.data.customers import create_customer


# ── Data layer: customer hourly ──


class TestCustomerHourlyRate:
    async def test_allows_first_message(self, session):
        cid = await create_customer(session)
        assert await check_and_increment_customer_rate(session, cid, max_messages=5) is True

    async def test_blocks_at_limit(self, session):
        cid = await create_customer(session)
        for _ in range(5):
            assert await check_and_increment_customer_rate(session, cid, max_messages=5) is True
        assert await check_and_increment_customer_rate(session, cid, max_messages=5) is False

    async def test_resets_after_window_expires(self, session):
        cid = await create_customer(session)
        for _ in range(5):
            await check_and_increment_customer_rate(session, cid, max_messages=5)
        assert await check_and_increment_customer_rate(session, cid, max_messages=5) is False

        await session.execute(
            update(RateLimit)
            .where(RateLimit.customer_id == cid, RateLimit.counter_type == "customer_hourly")
            .values(window_start=datetime.now(timezone.utc) - timedelta(minutes=61))
        )
        await session.commit()

        assert await check_and_increment_customer_rate(session, cid, max_messages=5) is True
        row = (
            await session.execute(
                select(RateLimit).where(
                    RateLimit.customer_id == cid, RateLimit.counter_type == "customer_hourly"
                )
            )
        ).scalars().first()
        assert row.message_count == 1

    async def test_independent_counters_per_customer(self, session):
        cid1 = await create_customer(session)
        cid2 = await create_customer(session)
        for _ in range(5):
            await check_and_increment_customer_rate(session, cid1, max_messages=5)
        assert await check_and_increment_customer_rate(session, cid1, max_messages=5) is False
        assert await check_and_increment_customer_rate(session, cid2, max_messages=5) is True


# ── Data layer: global daily ──


class TestGlobalDailyRate:
    async def _clear_global(self, session):
        await session.execute(
            delete(RateLimit).where(
                RateLimit.counter_type == "global_daily", RateLimit.customer_id.is_(None)
            )
        )
        await session.commit()

    async def test_allows_first_message(self, session):
        await self._clear_global(session)
        assert await check_and_increment_global_daily(session, max_messages=5) is True

    async def test_blocks_at_limit(self, session):
        await self._clear_global(session)
        for _ in range(5):
            assert await check_and_increment_global_daily(session, max_messages=5) is True
        assert await check_and_increment_global_daily(session, max_messages=5) is False

    async def test_resets_after_midnight_ist(self, session):
        await self._clear_global(session)
        for _ in range(5):
            await check_and_increment_global_daily(session, max_messages=5)
        assert await check_and_increment_global_daily(session, max_messages=5) is False

        yesterday_midnight = _latest_midnight_ist() - timedelta(days=1)
        await session.execute(
            update(RateLimit)
            .where(RateLimit.counter_type == "global_daily", RateLimit.customer_id.is_(None))
            .values(window_start=yesterday_midnight)
        )
        await session.commit()

        assert await check_and_increment_global_daily(session, max_messages=5) is True
        row = (
            await session.execute(
                select(RateLimit).where(
                    RateLimit.counter_type == "global_daily", RateLimit.customer_id.is_(None)
                )
            )
        ).scalars().first()
        assert row.message_count == 1


# ── Chat endpoint integration ──


class TestChatRateLimits:
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

    def _auth(self, client) -> dict:
        resp = client.post("/auth/signup", json={
            "name": "Test", "email": "ratelimit@test.com", "password": "password123",
        })
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def _auth_second(self, client) -> dict:
        resp = client.post("/auth/signup", json={
            "name": "Second", "email": "ratelimit2@test.com", "password": "password123",
        })
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    @patch("app.api.chat.run_agent_loop", new_callable=AsyncMock)
    def test_message_too_long_returns_400(self, mock_loop, client):
        headers = self._auth(client)
        long_msg = "a" * 2001
        resp = client.post("/chat", json={"message": long_msg}, headers=headers)
        assert resp.status_code == 400
        assert "too long" in resp.json()["detail"].lower()
        mock_loop.assert_not_called()

    @patch("app.api.chat.run_agent_loop", new_callable=AsyncMock)
    def test_message_at_exact_limit_succeeds(self, mock_loop, client):
        mock_loop.return_value = {"reply_text": "ok", "cards": []}
        headers = self._auth(client)
        exact_msg = "a" * 2000
        resp = client.post("/chat", json={"message": exact_msg}, headers=headers)
        assert resp.status_code == 200

    @patch("app.api.chat.check_and_increment_global_daily", new_callable=AsyncMock, return_value=True)
    @patch("app.api.chat.check_and_increment_customer_rate", new_callable=AsyncMock, return_value=False)
    @patch("app.api.chat.run_agent_loop", new_callable=AsyncMock)
    def test_customer_hourly_limit_returns_429(self, mock_loop, mock_customer, mock_global, client):
        headers = self._auth(client)
        resp = client.post("/chat", json={"message": "hello"}, headers=headers)
        assert resp.status_code == 429
        assert "wait" in resp.json()["reply_text"].lower()
        mock_loop.assert_not_called()

    @patch("app.api.chat.check_and_increment_global_daily", new_callable=AsyncMock, return_value=False)
    @patch("app.api.chat.run_agent_loop", new_callable=AsyncMock)
    def test_global_daily_limit_returns_429(self, mock_loop, mock_global, client):
        headers = self._auth(client)
        resp = client.post("/chat", json={"message": "hello"}, headers=headers)
        assert resp.status_code == 429
        assert "daily limit" in resp.json()["reply_text"].lower()
        mock_loop.assert_not_called()

    @patch("app.api.chat.check_and_increment_customer_rate", new_callable=AsyncMock, return_value=True)
    @patch("app.api.chat.check_and_increment_global_daily", new_callable=AsyncMock, return_value=False)
    @patch("app.api.chat.run_agent_loop", new_callable=AsyncMock)
    def test_global_cap_does_not_increment_customer_counter(self, mock_loop, mock_global, mock_customer, client):
        headers = self._auth(client)
        resp = client.post("/chat", json={"message": "hello"}, headers=headers)
        assert resp.status_code == 429
        assert "daily limit" in resp.json()["reply_text"].lower()
        mock_customer.assert_not_called()
