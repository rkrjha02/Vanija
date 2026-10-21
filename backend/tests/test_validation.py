from app.agent.validation import validate_tool_call
from app.tools.definitions import VALID_CATEGORIES

VALID_CATEGORIES.clear()
VALID_CATEGORIES.extend(["phone", "laptop", "headphone"])


def test_unknown_tool():
    _, error = validate_tool_call("fake_tool", {})
    assert error == "Unknown tool: fake_tool"


def test_strips_customer_id():
    args, error = validate_tool_call(
        "search_products", {"category": "phone", "customer_id": "abc123"}
    )
    assert error is None
    assert "customer_id" not in args


def test_search_valid():
    args, error = validate_tool_call(
        "search_products", {"category": "phone", "max_price": 15000}
    )
    assert error is None
    assert args["category"] == "phone"


def test_search_missing_category():
    _, error = validate_tool_call("search_products", {})
    assert "category" in error


def test_search_invalid_category():
    _, error = validate_tool_call("search_products", {"category": "tablet"})
    assert "must be one of" in error


def test_search_invalid_limit():
    _, error = validate_tool_call(
        "search_products", {"category": "phone", "limit": 99}
    )
    assert "limit" in error


def test_details_valid():
    args, error = validate_tool_call(
        "get_product_details", {"product_ids": ["PHN001"]}
    )
    assert error is None


def test_details_too_many_ids():
    _, error = validate_tool_call(
        "get_product_details", {"product_ids": ["A", "B", "C", "D"]}
    )
    assert "1 to 3" in error


def test_details_missing_ids():
    _, error = validate_tool_call("get_product_details", {})
    assert "required" in error
