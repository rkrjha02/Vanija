from datetime import datetime, timedelta, timezone

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.data.models import RateLimit

IST = timezone(timedelta(hours=5, minutes=30))


def _latest_midnight_ist() -> datetime:
    now_ist = datetime.now(IST)
    midnight = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    return midnight.astimezone(timezone.utc)


async def check_and_increment_customer_rate(
    session: AsyncSession,
    customer_id: str,
    max_messages: int = 50,
    window_minutes: int = 60,
) -> bool:
    cutoff = func.now() - timedelta(minutes=window_minutes)

    row = (
        await session.execute(
            select(RateLimit)
            .where(
                RateLimit.counter_type == "customer_hourly",
                RateLimit.customer_id == customer_id,
            )
            .with_for_update()
        )
    ).scalars().first()

    if row is None:
        await session.execute(
            insert(RateLimit).values(
                customer_id=customer_id,
                counter_type="customer_hourly",
                window_start=func.now(),
                message_count=1,
            )
        )
        await session.commit()
        return True

    if row.window_start < datetime.now(timezone.utc) - timedelta(minutes=window_minutes):
        await session.execute(
            update(RateLimit)
            .where(RateLimit.id == row.id)
            .values(window_start=func.now(), message_count=1)
        )
        await session.commit()
        return True

    if row.message_count >= max_messages:
        await session.commit()
        return False

    await session.execute(
        update(RateLimit)
        .where(RateLimit.id == row.id)
        .values(message_count=RateLimit.message_count + 1)
    )
    await session.commit()
    return True


async def check_and_increment_global_daily(
    session: AsyncSession,
    max_messages: int = 50,
) -> bool:
    midnight = _latest_midnight_ist()

    row = (
        await session.execute(
            select(RateLimit)
            .where(
                RateLimit.counter_type == "global_daily",
                RateLimit.customer_id.is_(None),
            )
            .with_for_update()
        )
    ).scalars().first()

    if row is None:
        await session.execute(
            insert(RateLimit).values(
                customer_id=None,
                counter_type="global_daily",
                window_start=midnight,
                message_count=1,
            )
        )
        await session.commit()
        return True

    if row.window_start < midnight:
        await session.execute(
            update(RateLimit)
            .where(RateLimit.id == row.id)
            .values(window_start=midnight, message_count=1)
        )
        await session.commit()
        return True

    if row.message_count >= max_messages:
        await session.commit()
        return False

    await session.execute(
        update(RateLimit)
        .where(RateLimit.id == row.id)
        .values(message_count=RateLimit.message_count + 1)
    )
    await session.commit()
    return True
