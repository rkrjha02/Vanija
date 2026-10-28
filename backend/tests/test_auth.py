import pytest
from datetime import datetime, timedelta, timezone

from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import create_access_token, create_refresh_token, decode_token
from app.data.auth import (
    create_customer_for_user,
    create_user,
    get_customer_by_user_id,
    get_refresh_token,
    get_user_by_email,
    revoke_refresh_token,
    store_refresh_token,
)


class TestPasswords:
    def test_hash_and_verify(self):
        hashed = hash_password("mysecretpw")
        assert hashed != "mysecretpw"
        assert verify_password("mysecretpw", hashed)

    def test_wrong_password(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)


class TestTokens:
    def test_access_token_roundtrip(self):
        token = create_access_token("u1", "c1", role="customer")
        payload = decode_token(token)
        assert payload["user_id"] == "u1"
        assert payload["customer_id"] == "c1"
        assert payload["role"] == "customer"

    def test_refresh_token_roundtrip(self):
        jwt_str, token_id = create_refresh_token("u1")
        payload = decode_token(jwt_str)
        assert payload["user_id"] == "u1"
        assert payload["token_id"] == token_id

    def test_decode_invalid_token(self):
        with pytest.raises(Exception):
            decode_token("not.a.valid.token")


class TestAuthDataLayer:
    async def test_create_and_get_user(self, session):
        user = await create_user(session, "test@example.com", "hash123", "Test User")
        assert user["email"] == "test@example.com"
        assert user["name"] == "Test User"

        found = await get_user_by_email(session, "test@example.com")
        assert found is not None
        assert found["id"] == user["id"]

    async def test_get_nonexistent_user(self, session):
        result = await get_user_by_email(session, "no@one.com")
        assert result is None

    async def test_create_customer_for_user(self, session):
        user = await create_user(session, "cust@example.com", "hash", "Cust")
        customer = await create_customer_for_user(session, user["id"])
        assert customer["user_id"] == user["id"]

        found = await get_customer_by_user_id(session, user["id"])
        assert found is not None
        assert found["id"] == customer["id"]

    async def test_refresh_token_store_and_revoke(self, session):
        user = await create_user(session, "tok@example.com", "hash", "Tok")
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        await store_refresh_token(session, "tid1", user["id"], expires)

        stored = await get_refresh_token(session, "tid1")
        assert stored is not None
        assert stored["revoked"] is False

        await revoke_refresh_token(session, "tid1")
        stored2 = await get_refresh_token(session, "tid1")
        assert stored2["revoked"] is True

    async def test_get_nonexistent_refresh_token(self, session):
        result = await get_refresh_token(session, "nope")
        assert result is None


class TestAuthEndpoints:
    """Tests auth API endpoints using the FastAPI test client."""

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

    def test_signup_success(self, client):
        resp = client.post("/auth/signup", json={
            "name": "Alice", "email": "alice@example.com", "password": "password123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["name"] == "Alice"

    def test_signup_duplicate_email(self, client):
        client.post("/auth/signup", json={
            "name": "Bob", "email": "dup@example.com", "password": "password123",
        })
        resp = client.post("/auth/signup", json={
            "name": "Bob2", "email": "dup@example.com", "password": "password456",
        })
        assert resp.status_code == 409

    def test_signup_validation_empty_name(self, client):
        resp = client.post("/auth/signup", json={
            "name": "  ", "email": "a@b.com", "password": "password123",
        })
        assert resp.status_code == 400

    def test_signup_validation_bad_email(self, client):
        resp = client.post("/auth/signup", json={
            "name": "X", "email": "not-an-email", "password": "password123",
        })
        assert resp.status_code == 400

    def test_signup_validation_short_password(self, client):
        resp = client.post("/auth/signup", json={
            "name": "X", "email": "x@y.com", "password": "short",
        })
        assert resp.status_code == 400

    def test_login_success(self, client):
        client.post("/auth/signup", json={
            "name": "Carol", "email": "carol@example.com", "password": "password123",
        })
        resp = client.post("/auth/login", json={
            "email": "carol@example.com", "password": "password123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["name"] == "Carol"

    def test_login_wrong_password(self, client):
        client.post("/auth/signup", json={
            "name": "Dave", "email": "dave@example.com", "password": "password123",
        })
        resp = client.post("/auth/login", json={
            "email": "dave@example.com", "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/auth/login", json={
            "email": "ghost@example.com", "password": "password123",
        })
        assert resp.status_code == 401

    def test_refresh_success(self, client):
        signup_resp = client.post("/auth/signup", json={
            "name": "Eve", "email": "eve@example.com", "password": "password123",
        })
        refresh_token = signup_resp.json()["refresh_token"]

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["refresh_token"] != refresh_token

    def test_refresh_reuse_revoked(self, client):
        signup_resp = client.post("/auth/signup", json={
            "name": "Frank", "email": "frank@example.com", "password": "password123",
        })
        refresh_token = signup_resp.json()["refresh_token"]

        client.post("/auth/refresh", json={"refresh_token": refresh_token})
        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 401

    def test_refresh_invalid_token(self, client):
        resp = client.post("/auth/refresh", json={"refresh_token": "garbage"})
        assert resp.status_code == 401

    def test_logout_success(self, client):
        signup_resp = client.post("/auth/signup", json={
            "name": "Grace", "email": "grace@example.com", "password": "password123",
        })
        refresh_token = signup_resp.json()["refresh_token"]

        resp = client.post("/auth/logout", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out"

        resp2 = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp2.status_code == 401

    def test_logout_invalid_token(self, client):
        resp = client.post("/auth/logout", json={"refresh_token": "garbage"})
        assert resp.status_code == 200
