from sqlalchemy import update

from app.data.addresses import save_address
from app.data.cart import add_item, get_or_create_active_cart
from app.data.customers import create_customer
from app.data.models import Product
from app.data.orders import cancel_order, place_order_from_pending
from app.tools.order_tools import (
    handle_cancel_order,
    handle_place_order,
    handle_view_saved_addresses,
    validate_cancel_order,
    validate_place_order,
)

NEW_ADDR = {"delivery_name": "Ravi", "delivery_phone": "9876543210", "address_line": "12 MG Road",
            "city": "Pune", "state": "Maharashtra", "pincode": "411001"}
SAVED = {"recipient_name": "Asha", "phone": "9123456780", "address_line": "4 Park St",
         "city": "Kolkata", "state": "West Bengal", "pincode": "700016"}


async def _customer_with_cart(session, product_id="ORD001", qty=1) -> str:
    cid = await create_customer(session)
    cart = await get_or_create_active_cart(session, cid)
    await add_item(session, cart["id"], product_id, qty)
    return cid


class TestValidation:
    def test_both_address_kinds_rejected(self):
        assert "not both" in validate_place_order({"address_id": 1, "city": "Pune"})

    def test_address_id_must_be_int(self):
        assert validate_place_order({"address_id": "1"}) is not None

    def test_neither_is_not_a_validation_error(self):
        assert validate_place_order({}) is None

    def test_cancel_order_id_must_be_int(self):
        assert validate_cancel_order({"order_id": 0}) is not None
        assert validate_cancel_order({}) is None


class TestViewSavedAddresses:
    async def test_empty_then_success(self, session):
        cid = await create_customer(session)
        assert (await handle_view_saved_addresses(session, {}, cid))["status"] == "empty"
        await save_address(session, cid, SAVED)
        result = await handle_view_saved_addresses(session, {}, cid)
        assert result["status"] == "success"
        assert result["addresses"][0]["is_default"] is True


class TestPlaceOrderTool:
    async def test_cart_empty(self, order_session):
        cid = await create_customer(order_session)
        assert (await handle_place_order(order_session, NEW_ADDR, cid))["status"] == "cart_empty"

    async def test_delivery_details_needed_when_nothing_sent(self, order_session):
        cid = await _customer_with_cart(order_session)
        result = await handle_place_order(order_session, {}, cid)
        assert result["status"] == "delivery_details_needed"
        assert "pincode is missing" in result["problems"]

    async def test_invalid_phone_and_pincode(self, order_session):
        cid = await _customer_with_cart(order_session)
        result = await handle_place_order(
            order_session, {**NEW_ADDR, "delivery_phone": "12345", "pincode": "4110"}, cid
        )
        assert result["status"] == "delivery_details_needed"
        assert "delivery_phone must be 10 digits" in result["problems"]
        assert "pincode must be exactly 6 digits" in result["problems"]

    async def test_other_customers_address_not_found(self, order_session):
        owner = await create_customer(order_session)
        address_id = await save_address(order_session, owner, SAVED)
        cid = await _customer_with_cart(order_session)
        result = await handle_place_order(order_session, {"address_id": address_id}, cid)
        assert result == {"status": "address_not_found"}

    async def test_cart_problem_gives_no_confirmation(self, order_session):
        cid = await _customer_with_cart(order_session, qty=3)
        await order_session.execute(update(Product).where(Product.id == "ORD001").values(stock=1))
        await order_session.commit()
        result = await handle_place_order(order_session, NEW_ADDR, cid)
        assert result["status"] == "cart_problem"
        assert result["problems"][0]["problem"] == "not_enough_stock"
        assert "_private" not in result

    async def test_new_address_confirmation(self, order_session):
        cid = await _customer_with_cart(order_session, qty=2)
        result = await handle_place_order(order_session, NEW_ADDR, cid)
        assert result["status"] == "confirmation_required"
        assert result["summary"]["cart_total"] == 2000.0
        assert result["summary"]["payment"] == "Cash on Delivery"
        assert result["_private"]["is_new_address"] is True

    async def test_saved_address_confirmation(self, order_session):
        cid = await _customer_with_cart(order_session)
        address_id = await save_address(order_session, cid, SAVED)
        result = await handle_place_order(order_session, {"address_id": address_id}, cid)
        assert result["status"] == "confirmation_required"
        assert result["summary"]["delivery"]["city"] == "Kolkata"
        assert result["_private"]["is_new_address"] is False


class TestCancelOrderTool:
    async def _place(self, session, cid):
        cart = await get_or_create_active_cart(session, cid)
        await add_item(session, cart["id"], "ORD001", 1)
        tool = await handle_place_order(session, NEW_ADDR, cid)
        result = await place_order_from_pending(session, tool["_private"]["pending_id"], cid)
        return result["order"]["order_id"]

    async def test_no_cancellable_order(self, order_session):
        cid = await create_customer(order_session)
        assert (await handle_cancel_order(order_session, {}, cid))["status"] == "no_cancellable_order"

    async def test_single_order_needs_confirmation(self, order_session):
        cid = await create_customer(order_session)
        oid = await self._place(order_session, cid)
        result = await handle_cancel_order(order_session, {}, cid)
        assert result["status"] == "confirmation_required"
        assert result["order_id"] == oid
        assert result["total"] == 1000.0

    async def test_multiple_orders(self, order_session):
        cid = await create_customer(order_session)
        await self._place(order_session, cid)
        await self._place(order_session, cid)
        result = await handle_cancel_order(order_session, {}, cid)
        assert result["status"] == "multiple_orders"
        assert len(result["orders"]) == 2

    async def test_not_found_and_already_cancelled(self, order_session):
        cid = await create_customer(order_session)
        oid = await self._place(order_session, cid)
        other = await create_customer(order_session)
        assert (await handle_cancel_order(order_session, {"order_id": oid}, other))["status"] == "not_found"
        await cancel_order(order_session, oid, cid)
        assert (await handle_cancel_order(order_session, {"order_id": oid}, cid))["status"] == "already_cancelled"
