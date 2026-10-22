from datetime import timedelta

from sqlalchemy import func, select, update

from app.data.cart import add_item, get_active_cart, get_or_create_active_cart
from app.data.customers import create_customer
from app.data.models import PendingConfirmation, Product
from app.data.orders import (
    cancel_order,
    create_pending,
    get_order,
    get_pending,
    place_order_from_pending,
)

DELIVERY = {"name": "Ravi", "phone": "9876543210", "address_line": "12 MG Road",
            "city": "Pune", "state": "Maharashtra", "pincode": "411001"}


async def _stock(session, product_id):
    return (await session.execute(select(Product.stock).where(Product.id == product_id))).scalar()


async def _cart_with(session, items: dict) -> tuple[str, dict, int]:
    cid = await create_customer(session)
    cart = await get_or_create_active_cart(session, cid)
    for product_id, qty in items.items():
        await add_item(session, cart["id"], product_id, qty)
    total = 1000 * items.get("ORD001", 0) + 30000 * items.get("ORD002", 0)
    pending = await create_pending(session, cid, cart["id"], total, DELIVERY, True)
    return cid, cart, pending["id"]


class TestPlaceOrder:
    async def test_places_order_and_reduces_stock(self, order_session):
        cid, cart, pid = await _cart_with(order_session, {"ORD001": 2, "ORD002": 1})
        result = await place_order_from_pending(order_session, pid, cid)

        assert result["status"] == "placed"
        order = result["order"]
        assert order["total"] == 32000.0
        assert order["payment_method"] == "cod"
        assert order["delivery"]["pincode"] == "411001"
        assert {i["product_id"]: i["unit_price"] for i in order["items"]} == {"ORD001": 1000.0, "ORD002": 30000.0}
        assert await _stock(order_session, "ORD001") == 3
        assert await _stock(order_session, "ORD002") == 2
        assert await get_active_cart(order_session, cid) is None
        assert (await get_pending(order_session, pid, cid))["order_id"] == order["order_id"]

    async def test_second_confirm_creates_nothing(self, order_session):
        cid, _, pid = await _cart_with(order_session, {"ORD001": 1})
        await place_order_from_pending(order_session, pid, cid)
        again = await place_order_from_pending(order_session, pid, cid)

        assert again == {"status": "failed", "reason": "not_waiting"}
        assert await _stock(order_session, "ORD001") == 4

    async def test_expired_pending_creates_no_order(self, order_session):
        cid, _, pid = await _cart_with(order_session, {"ORD001": 1})
        await order_session.execute(
            update(PendingConfirmation)
            .where(PendingConfirmation.id == pid)
            .values(expires_at=func.now() - timedelta(minutes=1))
        )
        await order_session.commit()

        result = await place_order_from_pending(order_session, pid, cid)
        assert result["reason"] == "not_waiting"
        assert await _stock(order_session, "ORD001") == 5

    async def test_price_change_is_refused(self, order_session):
        cid, _, pid = await _cart_with(order_session, {"ORD001": 1})
        await order_session.execute(update(Product).where(Product.id == "ORD001").values(price=1200))
        await order_session.commit()

        result = await place_order_from_pending(order_session, pid, cid)
        assert result["reason"] == "total_changed"
        assert (await get_pending(order_session, pid, cid))["status"] == "waiting"

    async def test_short_stock_rolls_back_everything(self, order_session):
        cid, _, pid = await _cart_with(order_session, {"ORD001": 2, "ORD002": 3})
        await order_session.execute(update(Product).where(Product.id == "ORD002").values(stock=1))
        await order_session.commit()

        result = await place_order_from_pending(order_session, pid, cid)
        assert result["reason"] == "not_enough_stock"
        assert result["product_id"] == "ORD002"
        assert await _stock(order_session, "ORD001") == 5
        assert (await get_pending(order_session, pid, cid))["status"] == "waiting"
        assert await get_active_cart(order_session, cid) is not None

    async def test_other_customer_cannot_confirm(self, order_session):
        cid, _, pid = await _cart_with(order_session, {"ORD001": 1})
        other = await create_customer(order_session)
        result = await place_order_from_pending(order_session, pid, other)
        assert result["reason"] == "not_waiting"
        assert await get_pending(order_session, pid, other) is None


class TestCancelOrder:
    async def _placed(self, session):
        cid, _, pid = await _cart_with(session, {"ORD001": 2})
        result = await place_order_from_pending(session, pid, cid)
        return cid, result["order"]["order_id"]

    async def test_cancel_restores_stock(self, order_session):
        cid, oid = await self._placed(order_session)
        assert await _stock(order_session, "ORD001") == 3
        result = await cancel_order(order_session, oid, cid)
        assert result["status"] == "cancelled"
        assert await _stock(order_session, "ORD001") == 5

    async def test_double_cancel_happens_once(self, order_session):
        cid, oid = await self._placed(order_session)
        await cancel_order(order_session, oid, cid)
        again = await cancel_order(order_session, oid, cid)
        assert again["status"] == "already_cancelled"
        assert await _stock(order_session, "ORD001") == 5

    async def test_other_customer_gets_not_found(self, order_session):
        cid, oid = await self._placed(order_session)
        other = await create_customer(order_session)
        assert (await cancel_order(order_session, oid, other))["status"] == "not_found"
        assert await get_order(order_session, oid, other) is None
        assert (await get_order(order_session, oid, cid))["status"] == "placed"
