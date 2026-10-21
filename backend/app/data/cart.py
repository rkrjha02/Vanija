from decimal import Decimal

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import Cart, CartItem, Product


async def get_active_cart(session: AsyncSession, customer_id: str) -> dict | None:
    result = await session.execute(
        select(Cart).where(
            Cart.customer_id == customer_id,
            Cart.status == "active",
        )
    )
    cart = result.scalars().first()
    if cart is None:
        return None
    return {"id": cart.id, "customer_id": cart.customer_id, "status": cart.status}


async def get_or_create_active_cart(
    session: AsyncSession, customer_id: str
) -> dict:
    cart = await get_active_cart(session, customer_id)
    if cart is not None:
        return cart
    new_cart = Cart(customer_id=customer_id, status="active")
    session.add(new_cart)
    await session.commit()
    return {
        "id": new_cart.id,
        "customer_id": new_cart.customer_id,
        "status": new_cart.status,
    }


async def add_item(
    session: AsyncSession, cart_id: int, product_id: str, quantity: int
) -> dict:
    product = await session.execute(
        select(Product.stock, Product.is_active).where(Product.id == product_id)
    )
    row = product.first()
    if row is None:
        return {"status": "failed", "reason": "not_found"}
    if not row.is_active:
        return {"status": "failed", "reason": "not_found"}
    if row.stock == 0:
        return {"status": "failed", "reason": "out_of_stock"}

    existing = await session.execute(
        select(CartItem.quantity).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
    )
    existing_qty = existing.scalar() or 0
    new_total = existing_qty + quantity

    if new_total > row.stock:
        return {
            "status": "failed",
            "reason": "not_enough_stock",
            "units_left": row.stock,
        }

    stmt = pg_insert(CartItem).values(
        cart_id=cart_id, product_id=product_id, quantity=quantity
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_cart_item_product",
        set_={"quantity": CartItem.quantity + quantity},
    )
    await session.execute(stmt)
    await session.commit()
    return {"status": "success"}


async def update_item_quantity(
    session: AsyncSession, cart_id: int, product_id: str, new_quantity: int
) -> dict:
    if new_quantity == 0:
        return await remove_item(session, cart_id, product_id)

    existing = await session.execute(
        select(CartItem.id).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
    )
    if existing.scalar() is None:
        return {"status": "failed", "reason": "not_in_cart"}

    product = await session.execute(
        select(Product.stock).where(Product.id == product_id)
    )
    stock = product.scalar()
    if new_quantity > stock:
        return {
            "status": "failed",
            "reason": "not_enough_stock",
            "units_left": stock,
        }

    await session.execute(
        update(CartItem)
        .where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        .values(quantity=new_quantity)
    )
    await session.commit()
    return {"status": "success"}


async def remove_item(
    session: AsyncSession, cart_id: int, product_id: str
) -> dict:
    result = await session.execute(
        delete(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
    )
    await session.commit()
    if result.rowcount == 0:
        return {"status": "failed", "reason": "not_in_cart"}
    return {"status": "success"}


async def get_cart_items(session: AsyncSession, cart_id: int) -> list[dict]:
    result = await session.execute(
        select(
            CartItem.product_id,
            Product.name,
            CartItem.quantity,
            Product.price,
            Product.stock,
            Product.is_active,
        )
        .join(Product, CartItem.product_id == Product.id)
        .where(CartItem.cart_id == cart_id)
    )
    items = []
    for row in result.all():
        unit_price = float(row.price) if isinstance(row.price, Decimal) else row.price
        line_total = round(unit_price * row.quantity, 2)

        problem = ""
        if not row.is_active:
            problem = "inactive"
        elif row.stock == 0:
            problem = "out_of_stock"
        elif row.stock < row.quantity:
            problem = "not_enough_stock"

        item = {
            "product_id": row.product_id,
            "name": row.name,
            "quantity": row.quantity,
            "unit_price": unit_price,
            "line_total": line_total,
            "problem": problem,
        }
        if problem == "not_enough_stock":
            item["units_left"] = row.stock
        items.append(item)
    return items


async def get_cart_summary(
    session: AsyncSession, customer_id: str
) -> dict:
    cart = await get_active_cart(session, customer_id)
    if cart is None:
        return {"status": "empty", "items": [], "cart_total": 0, "has_problems": False}

    items = await get_cart_items(session, cart["id"])
    if not items:
        return {"status": "empty", "items": [], "cart_total": 0, "has_problems": False}

    cart_total = round(sum(item["line_total"] for item in items), 2)
    has_problems = any(item["problem"] for item in items)
    return {
        "status": "success",
        "items": items,
        "cart_total": cart_total,
        "has_problems": has_problems,
    }
