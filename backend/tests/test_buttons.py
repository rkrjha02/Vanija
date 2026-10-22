from datetime import timedelta

from sqlalchemy import func, update

from app.agent.buttons import confirm_cancel, confirm_order
from app.data.addresses import list_addresses, save_address
from app.data.cart import add_item, get_or_create_active_cart
from app.data.customers import create_customer
from app.data.models import PendingConfirmation, Product
from app.data.orders import get_pending
from app.tools.order_tools import handle_place_order

NEW_ADDR = {"delivery_name": "Ravi", "delivery_phone": "9876543210", "address_line": "12 MG Road",
            "city": "Pune", "state": "Maharashtra", "pincode": "411001"}
SAVED = {"recipient_name": "Asha", "phone": "9123456780", "address_line": "4 Park St",
         "city": "Kolkata", "state": "West Bengal", "pincode": "700016"}


async def _prepared(session, args=None) -> tuple[str, int]:
    cid = await create_customer(session)
    cart = await get_or_create_active_cart(session, cid)
    await add_item(session, cart["id"], "ORD001", 1)
    if args is None:
        args = NEW_ADDR
    elif args == "saved":
        args = {"address_id": await save_address(session, cid, SAVED)}
    tool = await handle_place_order(session, args, cid)
    return cid, tool["_private"]["pending_id"]


class TestConfirmOrder:
    async def test_confirm_and_save_new_address(self, order_session):
        cid, pid = await _prepared(order_session)
        result = await confirm_order(order_session, cid, pid, True)
        assert result["status"] == "placed"
        assert result["cards"][0]["type"] == "order_placed"
        assert [a["city"] for a in await list_addresses(order_session, cid)] == ["Pune"]

    async def test_confirm_without_saving(self, order_session):
        cid, pid = await _prepared(order_session)
        await confirm_order(order_session, cid, pid, False)
        assert await list_addresses(order_session, cid) == []

    async def test_save_flag_ignored_for_saved_address(self, order_session):
        cid, pid = await _prepared(order_session, "saved")
        result = await confirm_order(order_session, cid, pid, True)
        assert result["status"] == "placed"
        assert len(await list_addresses(order_session, cid)) == 1

    async def test_double_tap_returns_already_placed(self, order_session):
        cid, pid = await _prepared(order_session)
        first = await confirm_order(order_session, cid, pid, False)
        second = await confirm_order(order_session, cid, pid, False)
        assert second["status"] == "already_placed"
        assert second["cards"][0]["order_id"] == first["cards"][0]["order_id"]

    async def test_price_change_gives_fresh_summary(self, order_session):
        cid, pid = await _prepared(order_session)
        await order_session.execute(update(Product).where(Product.id == "ORD001").values(price=1500))
        await order_session.commit()

        result = await confirm_order(order_session, cid, pid, False)
        assert result["status"] == "needs_reconfirm"
        assert result["reason"] == "total_changed"
        assert (result["previous_total"], result["new_total"]) == (1000.0, 1500.0)
        card = result["cards"][0]
        assert card["type"] == "order_confirmation"
        assert card["pending_id"] != pid
        assert (await get_pending(order_session, pid, cid))["status"] == "expired"

    async def test_expired_gives_fresh_summary(self, order_session):
        cid, pid = await _prepared(order_session)
        await order_session.execute(
            update(PendingConfirmation)
            .where(PendingConfirmation.id == pid)
            .values(expires_at=func.now() - timedelta(minutes=1))
        )
        await order_session.commit()

        result = await confirm_order(order_session, cid, pid, False)
        assert result["status"] == "needs_reconfirm"
        assert result["reason"] == "expired"
        assert result["cards"][0]["show_save_address"] is True

    async def test_cart_problem_gives_no_button(self, order_session):
        cid, pid = await _prepared(order_session)
        await order_session.execute(update(Product).where(Product.id == "ORD001").values(stock=0))
        await order_session.commit()

        result = await confirm_order(order_session, cid, pid, False)
        assert result["status"] == "cart_problem"
        assert result["cards"] == []

    async def test_other_customer_not_found(self, order_session):
        _, pid = await _prepared(order_session)
        other = await create_customer(order_session)
        assert (await confirm_order(order_session, other, pid, False))["status"] == "not_found"


class TestConfirmCancel:
    async def test_cancel_then_already_cancelled(self, order_session):
        cid, pid = await _prepared(order_session)
        placed = await confirm_order(order_session, cid, pid, False)
        oid = placed["cards"][0]["order_id"]

        first = await confirm_cancel(order_session, cid, oid)
        assert first["status"] == "cancelled"
        assert first["cards"][0]["type"] == "order_cancelled"
        assert (await confirm_cancel(order_session, cid, oid))["status"] == "already_cancelled"

    async def test_unknown_order(self, order_session):
        cid = await create_customer(order_session)
        assert (await confirm_cancel(order_session, cid, 999999))["status"] == "not_found"
