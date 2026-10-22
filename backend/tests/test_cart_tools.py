from app.data.customers import create_customer
from app.tools.cart_tools import (
    handle_add_to_cart,
    handle_update_cart_item,
    handle_view_cart,
)


class TestHandleAddToCart:
    async def test_add_success(self, seeded_session):
        cid = await create_customer(seeded_session)
        result = await handle_add_to_cart(
            seeded_session, {"product_id": "PHN001", "quantity": 1}, cid
        )
        assert result["status"] == "success"
        assert len(result["items"]) == 1
        assert result["items"][0]["product_id"] == "PHN001"

    async def test_add_out_of_stock(self, seeded_session):
        cid = await create_customer(seeded_session)
        result = await handle_add_to_cart(
            seeded_session, {"product_id": "PHN003"}, cid
        )
        assert result["status"] == "failed"
        assert result["reason"] == "out_of_stock"

    async def test_add_not_found(self, seeded_session):
        cid = await create_customer(seeded_session)
        result = await handle_add_to_cart(
            seeded_session, {"product_id": "FAKE999"}, cid
        )
        assert result["status"] == "failed"
        assert result["reason"] == "not_found"

    async def test_add_default_quantity(self, seeded_session):
        cid = await create_customer(seeded_session)
        result = await handle_add_to_cart(
            seeded_session, {"product_id": "PHN001"}, cid
        )
        assert result["status"] == "success"
        assert result["items"][0]["quantity"] == 1


class TestHandleUpdateCartItem:
    async def test_update_success(self, seeded_session):
        cid = await create_customer(seeded_session)
        await handle_add_to_cart(
            seeded_session, {"product_id": "PHN001", "quantity": 1}, cid
        )
        result = await handle_update_cart_item(
            seeded_session, {"product_id": "PHN001", "quantity": 3}, cid
        )
        assert result["status"] == "success"
        assert result["items"][0]["quantity"] == 3

    async def test_update_to_zero_removes(self, seeded_session):
        cid = await create_customer(seeded_session)
        await handle_add_to_cart(
            seeded_session, {"product_id": "PHN001", "quantity": 1}, cid
        )
        result = await handle_update_cart_item(
            seeded_session, {"product_id": "PHN001", "quantity": 0}, cid
        )
        assert result["status"] == "empty"
        assert result["items"] == []

    async def test_update_not_in_cart(self, seeded_session):
        cid = await create_customer(seeded_session)
        result = await handle_update_cart_item(
            seeded_session, {"product_id": "PHN001", "quantity": 2}, cid
        )
        assert result["status"] == "failed"
        assert result["reason"] == "not_in_cart"


class TestHandleViewCart:
    async def test_view_empty(self, session):
        cid = await create_customer(session)
        result = await handle_view_cart(session, {}, cid)
        assert result["status"] == "empty"

    async def test_view_with_items(self, seeded_session):
        cid = await create_customer(seeded_session)
        await handle_add_to_cart(
            seeded_session, {"product_id": "PHN001", "quantity": 2}, cid
        )
        result = await handle_view_cart(seeded_session, {}, cid)
        assert result["status"] == "success"
        assert result["cart_total"] == 9999.0 * 2
