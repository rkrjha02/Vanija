from app.data.cart import (
    add_item,
    get_active_cart,
    get_cart_items,
    get_cart_summary,
    get_or_create_active_cart,
    remove_item,
    update_item_quantity,
)
from app.data.customers import create_customer


class TestCartCreation:
    async def test_no_active_cart(self, session):
        cid = await create_customer(session)
        cart = await get_active_cart(session, cid)
        assert cart is None

    async def test_create_cart(self, session):
        cid = await create_customer(session)
        cart = await get_or_create_active_cart(session, cid)
        assert cart["customer_id"] == cid
        assert cart["status"] == "active"

    async def test_get_existing_cart(self, session):
        cid = await create_customer(session)
        cart1 = await get_or_create_active_cart(session, cid)
        cart2 = await get_or_create_active_cart(session, cid)
        assert cart1["id"] == cart2["id"]


class TestAddItem:
    async def test_add_success(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        result = await add_item(seeded_session, cart["id"], "PHN001", 1)
        assert result["status"] == "success"

    async def test_add_increases_quantity(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        await add_item(seeded_session, cart["id"], "PHN001", 2)
        await add_item(seeded_session, cart["id"], "PHN001", 3)
        items = await get_cart_items(seeded_session, cart["id"])
        phn001 = [i for i in items if i["product_id"] == "PHN001"][0]
        assert phn001["quantity"] == 5

    async def test_add_not_found(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        result = await add_item(seeded_session, cart["id"], "FAKE999", 1)
        assert result["status"] == "failed"
        assert result["reason"] == "not_found"

    async def test_add_out_of_stock(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        result = await add_item(seeded_session, cart["id"], "PHN003", 1)
        assert result["status"] == "failed"
        assert result["reason"] == "out_of_stock"

    async def test_add_not_enough_stock(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        result = await add_item(seeded_session, cart["id"], "PHN002", 99)
        assert result["status"] == "failed"
        assert result["reason"] == "not_enough_stock"
        assert result["units_left"] == 5

    async def test_add_inactive_product(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        result = await add_item(seeded_session, cart["id"], "PHN099", 1)
        assert result["status"] == "failed"
        assert result["reason"] == "not_found"


class TestUpdateItem:
    async def test_update_quantity(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        await add_item(seeded_session, cart["id"], "PHN001", 1)
        result = await update_item_quantity(seeded_session, cart["id"], "PHN001", 3)
        assert result["status"] == "success"
        items = await get_cart_items(seeded_session, cart["id"])
        assert items[0]["quantity"] == 3

    async def test_update_to_zero_removes(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        await add_item(seeded_session, cart["id"], "PHN001", 1)
        result = await update_item_quantity(seeded_session, cart["id"], "PHN001", 0)
        assert result["status"] == "success"
        items = await get_cart_items(seeded_session, cart["id"])
        assert len(items) == 0

    async def test_update_not_in_cart(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        result = await update_item_quantity(seeded_session, cart["id"], "PHN001", 5)
        assert result["status"] == "failed"
        assert result["reason"] == "not_in_cart"

    async def test_update_not_enough_stock(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        await add_item(seeded_session, cart["id"], "PHN002", 1)
        result = await update_item_quantity(seeded_session, cart["id"], "PHN002", 99)
        assert result["status"] == "failed"
        assert result["reason"] == "not_enough_stock"


class TestRemoveItem:
    async def test_remove_success(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        await add_item(seeded_session, cart["id"], "PHN001", 1)
        result = await remove_item(seeded_session, cart["id"], "PHN001")
        assert result["status"] == "success"

    async def test_remove_not_in_cart(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        result = await remove_item(seeded_session, cart["id"], "PHN001")
        assert result["status"] == "failed"
        assert result["reason"] == "not_in_cart"


class TestCartView:
    async def test_cart_items_with_prices(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        await add_item(seeded_session, cart["id"], "PHN001", 2)
        items = await get_cart_items(seeded_session, cart["id"])
        assert len(items) == 1
        assert items[0]["unit_price"] == 9999.0
        assert items[0]["line_total"] == 19998.0
        assert items[0]["problem"] == ""

    async def test_cart_summary(self, seeded_session):
        cid = await create_customer(seeded_session)
        cart = await get_or_create_active_cart(seeded_session, cid)
        await add_item(seeded_session, cart["id"], "PHN001", 1)
        await add_item(seeded_session, cart["id"], "HPH001", 2)
        summary = await get_cart_summary(seeded_session, cid)
        assert summary["status"] == "success"
        assert len(summary["items"]) == 2
        assert summary["cart_total"] == 9999.0 + 2999.0 * 2
        assert summary["has_problems"] is False

    async def test_cart_summary_empty(self, session):
        cid = await create_customer(session)
        summary = await get_cart_summary(session, cid)
        assert summary["status"] == "empty"
        assert summary["items"] == []
