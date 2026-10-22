import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.data.addresses import get_address_for_customer, list_addresses
from app.data.cart import get_active_cart, get_cart_summary
from app.data.orders import create_pending, get_order, list_placed_orders

NEW_ADDRESS_FIELDS = ("delivery_name", "delivery_phone", "address_line", "city", "state", "pincode")


def _is_positive_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def validate_view_saved_addresses(args: dict) -> str | None:
    return None


def validate_place_order(args: dict) -> str | None:
    has_id = args.get("address_id") is not None
    has_fields = any(args.get(f) for f in NEW_ADDRESS_FIELDS)
    if has_id and has_fields:
        return "send either address_id or the new address fields, not both"
    if has_id and not _is_positive_int(args["address_id"]):
        return "address_id must be a positive integer"
    for field in NEW_ADDRESS_FIELDS:
        if args.get(field) is not None and not isinstance(args[field], str):
            return f"{field} must be text"
    return None


def validate_cancel_order(args: dict) -> str | None:
    if args.get("order_id") is not None and not _is_positive_int(args["order_id"]):
        return "order_id must be a positive integer"
    return None


def _check_new_address(args: dict) -> tuple[dict | None, list[str]]:
    values = {f: (args.get(f) or "").strip() for f in NEW_ADDRESS_FIELDS}
    values["delivery_phone"] = re.sub(r"[\s-]", "", values["delivery_phone"])
    values["pincode"] = values["pincode"].replace(" ", "")

    problems = [f"{f} is missing" for f in NEW_ADDRESS_FIELDS if not values[f]]
    if values["delivery_phone"] and not re.fullmatch(r"\d{10}", values["delivery_phone"]):
        problems.append("delivery_phone must be 10 digits")
    if values["pincode"] and not re.fullmatch(r"\d{6}", values["pincode"]):
        problems.append("pincode must be exactly 6 digits")
    if problems:
        return None, problems
    return {
        "name": values["delivery_name"],
        "phone": values["delivery_phone"],
        "address_line": values["address_line"],
        "city": values["city"],
        "state": values["state"],
        "pincode": values["pincode"],
    }, []


def build_order_summary(cart_summary: dict, delivery: dict) -> dict:
    return {
        "items": [
            {
                "name": i["name"],
                "quantity": i["quantity"],
                "unit_price": i["unit_price"],
                "line_total": i["line_total"],
            }
            for i in cart_summary["items"]
        ],
        "cart_total": cart_summary["cart_total"],
        "delivery": delivery,
        "payment": "Cash on Delivery",
    }


async def prepare_confirmation(
    session: AsyncSession, customer_id: str, delivery: dict, is_new_address: bool
) -> dict:
    cart_summary = await get_cart_summary(session, customer_id)
    if cart_summary["status"] == "empty":
        return {"status": "cart_empty"}
    if cart_summary["has_problems"]:
        return {
            "status": "cart_problem",
            "problems": [
                {"name": i["name"], "problem": i["problem"], **({"units_left": i["units_left"]} if "units_left" in i else {})}
                for i in cart_summary["items"]
                if i["problem"]
            ],
        }

    cart = await get_active_cart(session, customer_id)
    pending = await create_pending(
        session, customer_id, cart["id"], cart_summary["cart_total"], delivery, is_new_address
    )
    return {
        "status": "confirmation_required",
        "summary": build_order_summary(cart_summary, delivery),
        "_private": {
            "pending_id": pending["id"],
            "expires_at": pending["expires_at"],
            "is_new_address": is_new_address,
        },
    }


async def handle_view_saved_addresses(
    session: AsyncSession, args: dict, customer_id: str
) -> dict:
    addresses = await list_addresses(session, customer_id)
    if not addresses:
        return {"status": "empty", "addresses": []}
    return {"status": "success", "addresses": addresses}


async def handle_place_order(
    session: AsyncSession, args: dict, customer_id: str
) -> dict:
    cart_summary = await get_cart_summary(session, customer_id)
    if cart_summary["status"] == "empty":
        return {"status": "cart_empty"}

    if args.get("address_id") is not None:
        address = await get_address_for_customer(session, args["address_id"], customer_id)
        if address is None:
            return {"status": "address_not_found"}
        delivery = {
            "name": address["recipient_name"],
            "phone": address["phone"],
            "address_line": address["address_line"],
            "city": address["city"],
            "state": address["state"],
            "pincode": address["pincode"],
        }
        return await prepare_confirmation(session, customer_id, delivery, is_new_address=False)

    delivery, problems = _check_new_address(args)
    if problems:
        return {"status": "delivery_details_needed", "problems": problems}
    return await prepare_confirmation(session, customer_id, delivery, is_new_address=True)


def _cancel_summary(order: dict) -> dict:
    return {
        "status": "confirmation_required",
        "order_id": order["order_id"],
        "items": [{"name": i["name"], "quantity": i["quantity"]} for i in order["items"]],
        "total": order["total"],
    }


async def handle_cancel_order(
    session: AsyncSession, args: dict, customer_id: str
) -> dict:
    order_id = args.get("order_id")
    if order_id is not None:
        order = await get_order(session, order_id, customer_id)
        if order is None:
            return {"status": "not_found"}
        if order["status"] == "cancelled":
            return {"status": "already_cancelled", "order_id": order_id}
        return _cancel_summary(order)

    placed = await list_placed_orders(session, customer_id)
    if not placed:
        return {"status": "no_cancellable_order"}
    if len(placed) > 1:
        return {"status": "multiple_orders", "orders": placed}
    order = await get_order(session, placed[0]["order_id"], customer_id)
    return _cancel_summary(order)


TOOL_HANDLERS = {
    "view_saved_addresses": {
        "validate": validate_view_saved_addresses,
        "handle": handle_view_saved_addresses,
    },
    "place_order": {
        "validate": validate_place_order,
        "handle": handle_place_order,
    },
    "cancel_order": {
        "validate": validate_cancel_order,
        "handle": handle_cancel_order,
    },
}
