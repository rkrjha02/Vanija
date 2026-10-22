from datetime import timedelta
from decimal import Decimal

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.config import settings
from app.data.models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    PendingConfirmation,
    Product,
)

DELIVERY_KEYS = ("name", "phone", "address_line", "city", "state", "pincode")


def _money(value) -> float:
    return float(round(Decimal(value), 2))


def _delivery_columns(delivery: dict) -> dict:
    return {f"delivery_{key}": delivery[key] for key in DELIVERY_KEYS}


def _delivery_from(row) -> dict:
    return {key: getattr(row, f"delivery_{key}") for key in DELIVERY_KEYS}


async def create_pending(
    session: AsyncSession,
    customer_id: str,
    cart_id: int,
    total: float,
    delivery: dict,
    is_new_address: bool,
) -> dict:
    await session.execute(
        update(PendingConfirmation)
        .where(
            PendingConfirmation.customer_id == customer_id,
            PendingConfirmation.status == "waiting",
        )
        .values(status="expired")
    )
    result = await session.execute(
        insert(PendingConfirmation)
        .values(
            customer_id=customer_id,
            cart_id=cart_id,
            total_shown=Decimal(str(total)),
            is_new_address=is_new_address,
            expires_at=func.now() + timedelta(minutes=settings.pending_expiry_minutes),
            status="waiting",
            **_delivery_columns(delivery),
        )
        .returning(PendingConfirmation.id, PendingConfirmation.expires_at)
    )
    row = result.one()
    await session.commit()
    return {"id": row.id, "expires_at": row.expires_at.isoformat()}


async def get_pending(
    session: AsyncSession, pending_id: int, customer_id: str
) -> dict | None:
    result = await session.execute(
        select(
            PendingConfirmation,
            (PendingConfirmation.expires_at <= func.now()).label("is_expired"),
        ).where(
            PendingConfirmation.id == pending_id,
            PendingConfirmation.customer_id == customer_id,
        )
    )
    row = result.first()
    if row is None:
        return None
    p = row[0]
    return {
        "id": p.id,
        "cart_id": p.cart_id,
        "total_shown": _money(p.total_shown),
        "delivery": _delivery_from(p),
        "is_new_address": p.is_new_address,
        "status": p.status,
        "is_expired": row.is_expired,
        "order_id": p.order_id,
    }


async def expire_pending(session: AsyncSession, pending_id: int) -> None:
    await session.execute(
        update(PendingConfirmation)
        .where(
            PendingConfirmation.id == pending_id,
            PendingConfirmation.status == "waiting",
        )
        .values(status="expired")
    )
    await session.commit()


async def place_order_from_pending(
    session: AsyncSession, pending_id: int, customer_id: str
) -> dict:
    try:
        result = await _place_order_steps(session, pending_id, customer_id)
    except Exception:
        await session.rollback()
        raise
    if result["status"] != "placed":
        await session.rollback()
        return result
    await session.commit()
    result["order"] = await get_order(session, result.pop("order_id"), customer_id)
    return result


async def _place_order_steps(
    session: AsyncSession, pending_id: int, customer_id: str
) -> dict:
    # 1. Claim the pending record. Only the first request can change it from 'waiting'.
    claimed = await session.execute(
        update(PendingConfirmation)
        .where(
            PendingConfirmation.id == pending_id,
            PendingConfirmation.customer_id == customer_id,
            PendingConfirmation.status == "waiting",
            PendingConfirmation.expires_at > func.now(),
        )
        .values(status="used")
        .returning(
            PendingConfirmation.cart_id,
            PendingConfirmation.total_shown,
            *[getattr(PendingConfirmation, f"delivery_{k}") for k in DELIVERY_KEYS],
        )
    )
    pending = claimed.first()
    if pending is None:
        return {"status": "failed", "reason": "not_waiting"}

    # 2. Re-read the cart with live prices and compare with what the customer saw.
    rows = (
        await session.execute(
            select(
                CartItem.product_id,
                CartItem.quantity,
                Product.name,
                Product.price,
                Product.is_active,
            )
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.cart_id == pending.cart_id)
            .order_by(CartItem.product_id)
        )
    ).all()
    if not rows:
        return {"status": "failed", "reason": "cart_empty"}
    if any(not r.is_active for r in rows):
        return {"status": "failed", "reason": "cart_problem"}
    total = sum((r.price * r.quantity for r in rows), Decimal("0"))
    if total != pending.total_shown:
        return {"status": "failed", "reason": "total_changed"}

    # 3. Reduce stock, in sorted product-ID order to avoid deadlocks.
    for r in rows:
        changed = await session.execute(
            update(Product)
            .where(Product.id == r.product_id, Product.stock >= r.quantity)
            .values(stock=Product.stock - r.quantity)
        )
        if changed.rowcount != 1:
            return {"status": "failed", "reason": "not_enough_stock", "product_id": r.product_id}

    # 4. Create the order with a price and name snapshot.
    order_id = (
        await session.execute(
            insert(Order)
            .values(
                customer_id=customer_id,
                status="placed",
                total_amount=total,
                payment_method="cod",
                **_delivery_columns(_delivery_from(pending)),
            )
            .returning(Order.id)
        )
    ).scalar_one()
    await session.execute(
        insert(OrderItem),
        [
            {
                "order_id": order_id,
                "product_id": r.product_id,
                "product_name": r.name,
                "unit_price": r.price,
                "quantity": r.quantity,
            }
            for r in rows
        ],
    )

    # 5. Close the cart and link the pending record to the order.
    closed = await session.execute(
        update(Cart)
        .where(
            Cart.id == pending.cart_id,
            Cart.customer_id == customer_id,
            Cart.status == "active",
        )
        .values(status="ordered")
    )
    if closed.rowcount != 1:
        return {"status": "failed", "reason": "cart_changed"}
    await session.execute(
        update(PendingConfirmation)
        .where(PendingConfirmation.id == pending_id)
        .values(order_id=order_id)
    )
    return {"status": "placed", "order_id": order_id}


async def get_order(
    session: AsyncSession, order_id: int, customer_id: str
) -> dict | None:
    order = (
        await session.execute(
            select(Order).where(Order.id == order_id, Order.customer_id == customer_id)
        )
    ).scalars().first()
    if order is None:
        return None
    items = (
        await session.execute(
            select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.product_id)
        )
    ).scalars().all()
    return {
        "order_id": order.id,
        "status": order.status,
        "total": _money(order.total_amount),
        "payment_method": order.payment_method,
        "created_at": order.created_at.isoformat(),
        "delivery": _delivery_from(order),
        "items": [
            {
                "product_id": i.product_id,
                "name": i.product_name,
                "quantity": i.quantity,
                "unit_price": _money(i.unit_price),
                "line_total": _money(i.unit_price * i.quantity),
            }
            for i in items
        ],
    }


async def list_placed_orders(session: AsyncSession, customer_id: str) -> list[dict]:
    result = await session.execute(
        select(Order.id, Order.created_at, Order.total_amount)
        .where(Order.customer_id == customer_id, Order.status == "placed")
        .order_by(Order.id.desc())
    )
    return [
        {
            "order_id": r.id,
            "date": r.created_at.date().isoformat(),
            "total": _money(r.total_amount),
        }
        for r in result.all()
    ]


async def cancel_order(
    session: AsyncSession, order_id: int, customer_id: str
) -> dict:
    try:
        cancelled = await session.execute(
            update(Order)
            .where(
                Order.id == order_id,
                Order.customer_id == customer_id,
                Order.status == "placed",
            )
            .values(status="cancelled")
            .returning(Order.id)
        )
        if cancelled.first() is None:
            await session.rollback()
            existing = await get_order(session, order_id, customer_id)
            if existing is None:
                return {"status": "not_found"}
            return {"status": "already_cancelled", "order": existing}

        items = (
            await session.execute(
                select(OrderItem.product_id, OrderItem.quantity)
                .where(OrderItem.order_id == order_id)
                .order_by(OrderItem.product_id)
            )
        ).all()
        for item in items:
            await session.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(stock=Product.stock + item.quantity)
            )
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return {"status": "cancelled", "order": await get_order(session, order_id, customer_id)}
