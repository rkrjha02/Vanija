from fastapi import HTTPException, Request

from app.auth.tokens import decode_token


async def get_current_customer(request: Request) -> dict:
    token = _extract_token(request)
    payload = _decode_or_401(token)
    if payload.get("role") != "customer":
        raise HTTPException(status_code=401, detail="Not a customer token")
    user_id = payload.get("user_id")
    customer_id = payload.get("customer_id")
    if not user_id or not customer_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"user_id": user_id, "customer_id": customer_id}


async def get_current_admin(request: Request) -> dict:
    token = _extract_token(request)
    payload = _decode_or_401(token)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Not an admin token")
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"user_id": user_id}


def _extract_token(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return auth[7:]


def _decode_or_401(token: str) -> dict:
    try:
        return decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
