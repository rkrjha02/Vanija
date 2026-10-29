"""Tests for GET /history through the FastAPI test client. Uses the test database, no LLM calls."""

import pytest


class TestHistoryEndpoint:
    @pytest.fixture
    async def client(self, engine, setup_db):
        from fastapi.testclient import TestClient
        from sqlalchemy.ext.asyncio import AsyncSession
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

    def _headers(self, client) -> dict:
        resp = client.post("/auth/signup", json={
            "name": "Hana", "email": "hana@example.com", "password": "password123",
        })
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    def test_new_customer_gets_an_empty_page(self, client):
        resp = client.get("/history", headers=self._headers(client))
        assert resp.status_code == 200
        assert resp.json() == {"messages": [], "has_more": False}

    def test_before_must_be_a_positive_number(self, client):
        headers = self._headers(client)
        assert client.get("/history?before=0", headers=headers).status_code == 422
        assert client.get("/history?before=abc", headers=headers).status_code == 422

    def test_history_needs_login(self, client):
        assert client.get("/history").status_code == 401
