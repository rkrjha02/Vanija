from app.tools.cart_tools import (
    validate_add_to_cart,
    validate_update_cart_item,
    validate_view_cart,
)


class TestAddToCartValidation:
    def test_valid(self):
        assert validate_add_to_cart({"product_id": "PHN001"}) is None

    def test_valid_with_quantity(self):
        assert validate_add_to_cart({"product_id": "PHN001", "quantity": 3}) is None

    def test_missing_product_id(self):
        error = validate_add_to_cart({})
        assert "product_id" in error

    def test_invalid_quantity_zero(self):
        error = validate_add_to_cart({"product_id": "PHN001", "quantity": 0})
        assert "quantity" in error

    def test_invalid_quantity_too_high(self):
        error = validate_add_to_cart({"product_id": "PHN001", "quantity": 11})
        assert "quantity" in error


class TestUpdateCartItemValidation:
    def test_valid(self):
        assert validate_update_cart_item({"product_id": "PHN001", "quantity": 3}) is None

    def test_valid_zero_removes(self):
        assert validate_update_cart_item({"product_id": "PHN001", "quantity": 0}) is None

    def test_missing_product_id(self):
        error = validate_update_cart_item({"quantity": 1})
        assert "product_id" in error

    def test_missing_quantity(self):
        error = validate_update_cart_item({"product_id": "PHN001"})
        assert "quantity" in error

    def test_invalid_quantity_negative(self):
        error = validate_update_cart_item({"product_id": "PHN001", "quantity": -1})
        assert "quantity" in error

    def test_invalid_quantity_too_high(self):
        error = validate_update_cart_item({"product_id": "PHN001", "quantity": 11})
        assert "quantity" in error


class TestViewCartValidation:
    def test_valid_empty_args(self):
        assert validate_view_cart({}) is None
