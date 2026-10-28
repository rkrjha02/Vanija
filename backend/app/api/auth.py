import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.passwords import hash_password, verify_password
from app.auth.tokens import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings
from app.data.auth import (
    create_customer_for_user,
    create_user,
    get_customer_by_user_id,
    get_refresh_token,
    get_user_by_email,
    revoke_refresh_token,
    store_refresh_token,
)
from app.data.database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/signup")
async def signup(req: SignupRequest, session: AsyncSession = Depends(get_db)):
    name = req.name.strip()
    email = req.email.strip().lower()

    if not name:
        raise HTTPException(status_code=400, detail="Name is required")
    if not EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = await get_user_by_email(session, email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    pw_hash = hash_password(req.password)
    user = await create_user(session, email, pw_hash, name)
    customer = await create_customer_for_user(session, user["id"])

    access = create_access_token(user["id"], customer["id"])
    refresh_jwt, token_id = create_refresh_token(user["id"])
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    await store_refresh_token(session, token_id, user["id"], expires_at)

    await session.commit()

    return {"access_token": access, "refresh_token": refresh_jwt, "name": user["name"]}


@router.post("/login")
async def login(req: LoginRequest, session: AsyncSession = Depends(get_db)):
    email = req.email.strip().lower()
    user = await get_user_by_email(session, email)
    if not user or not user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    customer = await get_customer_by_user_id(session, user["id"])
    if not customer:
        raise HTTPException(status_code=500, detail="Customer record missing")

    access = create_access_token(user["id"], customer["id"])
    refresh_jwt, token_id = create_refresh_token(user["id"])
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    await store_refresh_token(session, token_id, user["id"], expires_at)

    await session.commit()

    return {"access_token": access, "refresh_token": refresh_jwt, "name": user["name"]}


@router.post("/refresh")
async def refresh(req: RefreshRequest, session: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    token_id = payload.get("token_id")
    user_id = payload.get("user_id")
    if not token_id or not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    stored = await get_refresh_token(session, token_id)
    if not stored or stored["revoked"]:
        raise HTTPException(status_code=401, detail="Refresh token revoked or not found")
    if stored["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    await revoke_refresh_token(session, token_id)

    customer = await get_customer_by_user_id(session, user_id)
    if not customer:
        raise HTTPException(status_code=500, detail="Customer record missing")

    new_access = create_access_token(user_id, customer["id"])
    new_refresh_jwt, new_token_id = create_refresh_token(user_id)
    new_expires = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    await store_refresh_token(session, new_token_id, user_id, new_expires)

    await session.commit()

    return {"access_token": new_access, "refresh_token": new_refresh_jwt}


@router.post("/logout")
async def logout(req: LogoutRequest, session: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(req.refresh_token)
    except Exception:
        return {"message": "Logged out"}

    token_id = payload.get("token_id")
    if token_id:
        await revoke_refresh_token(session, token_id)
        await session.commit()

    return {"message": "Logged out"}
