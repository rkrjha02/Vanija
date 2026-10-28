import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings

ALGORITHM = "HS256"


def create_access_token(user_id: str, customer_id: str, role: str = "customer") -> str:
    payload = {
        "user_id": user_id,
        "customer_id": customer_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def create_admin_access_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.admin_access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, str]:
    token_id = uuid.uuid4().hex
    payload = {
        "user_id": user_id,
        "token_id": token_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)
    return token, token_id


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
