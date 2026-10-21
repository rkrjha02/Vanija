from app.tools.definitions import VALID_CATEGORIES
from app.tools.product_tools import (
    build_search_label,
    handle_get_product_details,
    handle_search_products,
)

VALID_CATEGORIES.clear()
VALID_CATEGORIES.extend(["phone", "laptop", "headphone"])


class TestSearchProducts:
    async def test_success(self, seeded_session):
        result = await handle_search_products(
            seeded_session, {"category": "phone"}
        )
        assert result["status"] == "success"
        assert result["total_matches"] >= 2
        assert len(result["products"]) >= 2

    async def test_no_match(self, seeded_session):
        result = await handle_search_products(
            seeded_session, {"category": "phone", "max_price": 1}
        )
        assert result["status"] == "no_match"

    async def test_with_filters(self, seeded_session):
        result = await handle_search_products(
            seeded_session,
            {"category": "phone", "max_price": 10000, "brand": "Samsung"},
        )
        assert result["status"] == "success"
        for p in result["products"]:
            assert p["price"] <= 10000


class TestGetProductDetails:
    async def test_success(self, seeded_session):
        result = await handle_get_product_details(
            seeded_session, {"product_ids": ["PHN001"]}
        )
        assert result["status"] == "success"
        assert result["products"][0]["id"] == "PHN001"
        assert "description" in result["products"][0]

    async def test_not_found(self, seeded_session):
        result = await handle_get_product_details(
            seeded_session, {"product_ids": ["FAKE999"]}
        )
        assert result["products"][0]["status"] == "not_found"


class TestBuildSearchLabel:
    def test_basic(self):
        assert build_search_label({"category": "phone"}) == "phones"

    def test_with_max_price(self):
        label = build_search_label({"category": "phone", "max_price": 15000})
        assert "under" in label
        assert "15,000" in label

    def test_with_brand(self):
        label = build_search_label({"category": "laptop", "brand": "HP"})
        assert "HP" in label
        assert "laptops" in label

    def test_with_price_range(self):
        label = build_search_label(
            {"category": "phone", "min_price": 10000, "max_price": 20000}
        )
        assert "10,000" in label
        assert "20,000" in label
