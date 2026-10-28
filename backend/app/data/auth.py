import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Conversation, Customer, RefreshToken, User


async def create_user(
    session: AsyncSession,
    email: str,
    password_hash: str | None,
    name: str,
    auth_provider: str = "email",
) -> dict:
    user = User(
        id=uuid.uuid4().hex,
        email=email,
        password_hash=password_hash,
        name=name,
        auth_provider=auth_provider,
    )
    session.add(user)
    await session.flush()
    return {"id": user.id, "email": user.email, "name": user.name}


async def get_user_by_email(session: AsyncSession, email: str) -> dict | None:
    result = await session.execute(select(User).where(User.email == email))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return {
        "id": row.id,
        "email": row.email,
        "name": row.name,
        "password_hash": row.password_hash,
        "auth_provider": row.auth_provider,
    }


async def create_customer_for_user(session: AsyncSession, user_id: str) -> dict:
    customer_id = uuid.uuid4().hex
    customer = Customer(id=customer_id, user_id=user_id)
    session.add(customer)
    await session.flush()
    conversation = Conversation(customer_id=customer_id)
    session.add(conversation)
    await session.flush()
    return {"id": customer.id, "user_id": customer.user_id}


async def store_refresh_token(
    session: AsyncSession,
    token_id: str,
    user_id: str,
    expires_at: datetime,
) -> None:
    token = RefreshToken(id=token_id, user_id=user_id, expires_at=expires_at)
    session.add(token)
    await session.flush()


async def get_refresh_token(session: AsyncSession, token_id: str) -> dict | None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.id == token_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return {
        "id": row.id,
        "user_id": row.user_id,
        "expires_at": row.expires_at,
        "revoked": row.revoked,
    }


async def revoke_refresh_token(session: AsyncSession, token_id: str) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.id == token_id)
        .values(revoked=True)
    )
    await session.flush()


async def get_customer_by_user_id(session: AsyncSession, user_id: str) -> dict | None:
    result = await session.execute(
        select(Customer).where(Customer.user_id == user_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return {"id": row.id, "user_id": row.user_id, "name": row.name}
