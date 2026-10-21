from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Message


async def save_message(
    session: AsyncSession,
    conversation_id: int,
    turn_id: str,
    role: str,
    content: str | None = None,
    tool_calls: list | None = None,
    tool_call_id: str | None = None,
) -> None:
    msg = Message(
        conversation_id=conversation_id,
        turn_id=turn_id,
        role=role,
        content=content,
        tool_calls=tool_calls,
        tool_call_id=tool_call_id,
    )
    session.add(msg)
    await session.commit()


async def get_recent_messages(
    session: AsyncSession, conversation_id: int, limit: int
) -> list[dict]:
    result = await session.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.role.in_(["user", "assistant"]),
            Message.content.isnot(None),
        )
        .order_by(Message.id.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        {"role": row.role, "content": row.content}
        for row in reversed(rows)
    ]


async def get_turn_messages(
    session: AsyncSession, conversation_id: int, turn_id: str
) -> list[dict]:
    result = await session.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.turn_id == turn_id,
        )
        .order_by(Message.id.asc())
    )
    rows = result.scalars().all()

    messages = []
    for row in rows:
        msg = {"role": row.role, "content": row.content}
        if row.tool_calls:
            msg["tool_calls"] = row.tool_calls
        if row.tool_call_id:
            msg["tool_call_id"] = row.tool_call_id
        messages.append(msg)
    return messages
