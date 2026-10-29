from sqlalchemy import func, select
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
    cards: list | None = None,
) -> None:
    msg = Message(
        conversation_id=conversation_id,
        turn_id=turn_id,
        role=role,
        content=content,
        tool_calls=tool_calls,
        tool_call_id=tool_call_id,
        cards=cards or None,
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


async def get_history_page(
    session: AsyncSession, conversation_id: int, before_id: int | None, limit: int
) -> dict:
    """One page of the chat for the screen: customer messages and final replies only.

    before_id is the id of the oldest message the screen already has (None = newest page).
    Returns the page oldest-first, and has_more = True when even older messages exist.
    """
    query = (
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.role.in_(["user", "assistant"]),
            Message.content.isnot(None),
            Message.content != "",
            # Skip assistant rows that request tools; only final replies are shown.
            # A missing tool_calls value can be stored as SQL NULL or as JSON null.
            func.coalesce(func.jsonb_typeof(Message.tool_calls), "null") == "null",
        )
        .order_by(Message.id.desc())
        .limit(limit + 1)
    )
    if before_id is not None:
        query = query.where(Message.id < before_id)

    rows = (await session.execute(query)).scalars().all()
    # One extra row was asked for: if it came back, older messages exist.
    has_more = len(rows) > limit
    page = rows[:limit]
    return {
        "messages": [
            {"id": row.id, "role": row.role, "content": row.content, "cards": row.cards}
            for row in reversed(page)
        ],
        "has_more": has_more,
    }


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
