from sqlalchemy.ext.asyncio import AsyncSession

from app.data.cart import (
    add_item,
    get_cart_summary,
    get_or_create_active_cart,
    update_item_quantity,
)


def validate_add_to_cart(args: dict) -> str | None:
    if not args.get("product_id"):
        return "product_id is required"
    quantity = args.get("quantity", 1)
    if not isinstance(quantity, int) or quantity < 1 or quantity > 10:
        return "quantity must be between 1 and 10"
    return None


def validate_update_cart_item(args: dict) -> str | None:
    if not args.get("product_id"):
        return "product_id is required"
    quantity = args.get("quantity")
    if quantity is None:
        return "quantity is required"
    if not isinstance(quantity, int) or quantity < 0 or quantity > 10:
        return "quantity must be between 0 and 10"
    return None


def validate_view_cart(args: dict) -> str | None:
    return None


async def handle_add_to_cart(
    session: AsyncSession, args: dict, customer_id: str
) -> dict:
    cart = await get_or_create_active_cart(session, customer_id)

    quantity = args.get("quantity", 1)
    result = await add_item(session, cart["id"], args["product_id"], quantity)

    if result["status"] == "failed":
        return result

    summary = await get_cart_summary(session, customer_id)
    return summary


async def handle_update_cart_item(
    session: AsyncSession, args: dict, customer_id: str
) -> dict:
    cart = await get_or_create_active_cart(session, customer_id)

    result = await update_item_quantity(
        session, cart["id"], args["product_id"], args["quantity"]
    )

    if result["status"] == "failed":
        return result

    summary = await get_cart_summary(session, customer_id)
    return summary


async def handle_view_cart(
    session: AsyncSession, args: dict, customer_id: str
) -> dict:
    return await get_cart_summary(session, customer_id)


TOOL_HANDLERS = {
    "add_to_cart": {
        "validate": validate_add_to_cart,
        "handle": handle_add_to_cart,
    },
    "update_cart_item": {
        "validate": validate_update_cart_item,
        "handle": handle_update_cart_item,
    },
    "view_cart": {
        "validate": validate_view_cart,
        "handle": handle_view_cart,
    },
}
