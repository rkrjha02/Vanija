from app.data.cart import add_item, get_or_create_active_cart
from app.data.customers import create_customer
from app.data.orders import cancel_order, get_customer_orders, place_order_from_pending
from app.tools.order_tools import (
    handle_place_order,
    handle_view_orders,
    validate_view_orders,
)

NEW_ADDR = {
    "delivery_name": "Ravi", "delivery_phone": "9876543210",
    "address_line": "12 MG Road", "city": "Pune", "state": "Maharashtra", "pincode": "411001",
}


async def _place_order(session, cid, product_id="ORD001", qty=1):
    cart = await get_or_create_active_cart(session, cid)
    await add_item(session, cart["id"], product_id, qty)
    tool = await handle_place_order(session, NEW_ADDR, cid)
    result = await place_order_from_pending(session, tool["_private"]["pending_id"], cid)
    return result["order"]["order_id"]


class TestValidateViewOrders:
    def test_no_args_is_valid(self):
        assert validate_view_orders({}) is None

    def test_valid_status(self):
        assert validate_view_orders({"status": "placed"}) is None
        assert validate_view_orders({"status": "cancelled"}) is None

    def test_invalid_status(self):
        err = validate_view_orders({"status": "shipped"})
        assert err is not None
        assert "placed" in err


class TestGetCustomerOrders:
    async def test_returns_newest_first(self, order_session):
        cid = await create_customer(order_session)
        oid1 = await _place_order(order_session, cid)
        oid2 = await _place_order(order_session, cid)
        orders = await get_customer_orders(order_session, cid)
        assert len(orders) == 2
        assert orders[0]["order_id"] == oid2
        assert orders[1]["order_id"] == oid1

    async def test_status_filter_placed(self, order_session):
        cid = await create_customer(order_session)
        oid1 = await _place_order(order_session, cid)
        oid2 = await _place_order(order_session, cid)
        await cancel_order(order_session, oid1, cid)
        orders = await get_customer_orders(order_session, cid, status="placed")
        assert len(orders) == 1
        assert orders[0]["order_id"] == oid2

    async def test_status_filter_cancelled(self, order_session):
        cid = await create_customer(order_session)
        oid1 = await _place_order(order_session, cid)
        await _place_order(order_session, cid)
        await cancel_order(order_session, oid1, cid)
        orders = await get_customer_orders(order_session, cid, status="cancelled")
        assert len(orders) == 1
        assert orders[0]["status"] == "cancelled"

    async def test_limit_works(self, order_session):
        cid = await create_customer(order_session)
        await _place_order(order_session, cid)
        await _place_order(order_session, cid)
        await _place_order(order_session, cid)
        orders = await get_customer_orders(order_session, cid, limit=2)
        assert len(orders) == 2

    async def test_includes_items(self, order_session):
        cid = await create_customer(order_session)
        await _place_order(order_session, cid, qty=2)
        orders = await get_customer_orders(order_session, cid)
        assert len(orders[0]["items"]) == 1
        assert orders[0]["items"][0]["name"] == "Order Phone"
        assert orders[0]["items"][0]["quantity"] == 2
        assert orders[0]["items"][0]["price"] == 1000.0

    async def test_empty_when_no_orders(self, order_session):
        cid = await create_customer(order_session)
        orders = await get_customer_orders(order_session, cid)
        assert orders == []


class TestViewOrdersTool:
    async def test_returns_order_list_card(self, order_session):
        cid = await create_customer(order_session)
        await _place_order(order_session, cid)
        await _place_order(order_session, cid)
        result = await handle_view_orders(order_session, {}, cid)
        assert result["status"] == "success"
        assert len(result["orders"]) == 2
        assert result["orders"][0]["position"] == 1
        assert result["orders"][1]["position"] == 2
        card = result["_card"]
        assert card["type"] == "order_list"
        assert len(card["orders"]) == 2

    async def test_status_filter_excludes_cancelled(self, order_session):
        cid = await create_customer(order_session)
        oid = await _place_order(order_session, cid)
        await _place_order(order_session, cid)
        await cancel_order(order_session, oid, cid)
        result = await handle_view_orders(order_session, {"status": "placed"}, cid)
        assert result["status"] == "success"
        assert len(result["orders"]) == 1
        assert result["orders"][0]["status"] == "placed"

    async def test_empty_orders(self, order_session):
        cid = await create_customer(order_session)
        result = await handle_view_orders(order_session, {}, cid)
        assert result["status"] == "empty"
        assert result["orders"] == []
