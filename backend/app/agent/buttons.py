import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.loop import build_order_confirmation_card
from app.data.addresses import save_address
from app.data.conversations import get_or_create_conversation
from app.data.messages import save_message
from app.data.orders import (
    cancel_order,
    expire_pending,
    get_order,
    get_pending,
    place_order_from_pending,
)
from app.tools.order_tools import prepare_confirmation

logger = logging.getLogger(__name__)


def _order_card(card_type: str, order: dict) -> dict:
    return {
        "type": card_type,
        "order_id": order["order_id"],
        "status": order["status"],
        "total": order["total"],
        "items": order["items"],
        "delivery": order["delivery"],
    }


async def confirm_order(
    session: AsyncSession, customer_id: str, pending_id: int, save_new_address: bool
) -> dict:
    pending = await get_pending(session, pending_id, customer_id)
    if pending is None:
        return {"status": "not_found", "message": "This confirmation was not found.", "cards": []}

    if pending["status"] == "used":
        resp = await _already_placed(session, customer_id, pending["order_id"])
        await _save_button_result(session, customer_id, resp)
        return resp

    reason = "expired"
    if pending["status"] == "waiting" and not pending["is_expired"]:
        result = await place_order_from_pending(session, pending_id, customer_id)
        if result["status"] == "placed":
            order = result["order"]
            if save_new_address and pending["is_new_address"]:
                await _save_address_quietly(session, customer_id, pending["delivery"])
            resp = {
                "status": "placed",
                "message": f"Order #{order['order_id']} is placed. You will pay ₹{order['total']:,.2f} on delivery.",
                "cards": [_order_card("order_placed", order)],
            }
            await _save_button_result(session, customer_id, resp)
            return resp
        reason = result["reason"]
        if reason == "not_waiting":
            again = await get_pending(session, pending_id, customer_id)
            if again["status"] == "used":
                resp = await _already_placed(session, customer_id, again["order_id"])
                await _save_button_result(session, customer_id, resp)
                return resp
            reason = "expired"

    resp = await _fresh_summary(session, customer_id, pending, reason)
    await _save_button_result(session, customer_id, resp)
    return resp


async def _already_placed(session: AsyncSession, customer_id: str, order_id: int) -> dict:
    order = await get_order(session, order_id, customer_id)
    return {
        "status": "already_placed",
        "message": f"Order #{order_id} was already placed.",
        "cards": [_order_card("order_placed", order)],
    }


async def _save_address_quietly(session: AsyncSession, customer_id: str, delivery: dict) -> None:
    try:
        await save_address(session, customer_id, {
            "recipient_name": delivery["name"],
            "phone": delivery["phone"],
            "address_line": delivery["address_line"],
            "city": delivery["city"],
            "state": delivery["state"],
            "pincode": delivery["pincode"],
        })
    except Exception as e:
        logger.error("Saving address failed (order still placed): %s", e)
        await session.rollback()


async def _fresh_summary(
    session: AsyncSession, customer_id: str, pending: dict, reason: str
) -> dict:
    await expire_pending(session, pending["id"])
    fresh = await prepare_confirmation(
        session, customer_id, pending["delivery"], pending["is_new_address"]
    )

    if fresh["status"] == "cart_empty":
        return {"status": "cart_empty", "message": "Your cart is empty, so no order was placed.", "cards": []}
    if fresh["status"] == "cart_problem":
        return {
            "status": "cart_problem",
            "message": "Some items in your cart need attention before you can order. Please fix them in the chat.",
            "problems": fresh["problems"],
            "cards": [],
        }

    new_total = fresh["summary"]["cart_total"]
    if reason == "expired":
        message = "That confirmation expired. Here is a fresh summary. Please confirm again."
    else:
        message = "Something changed since you saw the summary. Please check it and confirm again."
    return {
        "status": "needs_reconfirm",
        "reason": reason,
        "previous_total": pending["total_shown"],
        "new_total": new_total,
        "message": message,
        "cards": [build_order_confirmation_card(fresh)],
    }


async def confirm_cancel(session: AsyncSession, customer_id: str, order_id: int) -> dict:
    result = await cancel_order(session, order_id, customer_id)
    if result["status"] == "not_found":
        return {"status": "not_found", "message": "This order was not found.", "cards": []}
    if result["status"] == "already_cancelled":
        resp = {
            "status": "already_cancelled",
            "message": f"Order #{order_id} was already cancelled.",
            "cards": [_order_card("order_cancelled", result["order"])],
        }
    else:
        resp = {
            "status": "cancelled",
            "message": f"Order #{order_id} is cancelled.",
            "cards": [_order_card("order_cancelled", result["order"])],
        }
    await _save_button_result(session, customer_id, resp)
    return resp


async def _save_button_result(session: AsyncSession, customer_id: str, result: dict) -> None:
    conv = await get_or_create_conversation(session, customer_id)
    turn_id = str(uuid.uuid4())
    await save_message(
        session, conv["id"], turn_id, "assistant",
        content=result["message"],
        cards=result.get("cards"),
    )
