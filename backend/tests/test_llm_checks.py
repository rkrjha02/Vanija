"""Unit tests for check functions in llm_test_set. No LLM or database calls."""

from tests.llm_test_set import (
    Case,
    _check_addresses_before_order,
    check_result,
)


class TestCurlyApostrophe:
    def test_curly_apostrophe_matches(self):
        """Reply with curly apostrophes should match straight-apostrophe phrases."""
        case = Case(
            name="test",
            message="Do you recycle old batteries?",
            expect_tool="search_policies",
            expect_reply_any=["don't have", "do not have", "no information"],
        )
        result = {"reply_text": "I’m sorry, I don’t have that information."}
        tool_calls = [{"name": "search_policies", "arguments": {"question": "recycle batteries"}}]
        ok, detail = check_result(case, result, tool_calls)
        assert ok, f"Should pass with curly apostrophe, got: {detail}"

    def test_straight_apostrophe_still_matches(self):
        case = Case(
            name="test",
            message="Do you recycle old batteries?",
            expect_tool="search_policies",
            expect_reply_any=["don't have", "do not have"],
        )
        result = {"reply_text": "I'm sorry, I don't have that information."}
        tool_calls = [{"name": "search_policies", "arguments": {"question": "recycle batteries"}}]
        ok, detail = check_result(case, result, tool_calls)
        assert ok


class TestAddressesBeforeOrder:
    def test_addresses_then_order_passes(self):
        calls = [
            {"name": "view_cart", "arguments": {}},
            {"name": "view_saved_addresses", "arguments": {}},
            {"name": "place_order", "arguments": {"address_id": 1}},
        ]
        ok, detail = _check_addresses_before_order(calls)
        assert ok, detail

    def test_addresses_without_order_passes(self):
        calls = [
            {"name": "view_cart", "arguments": {}},
            {"name": "view_saved_addresses", "arguments": {}},
        ]
        ok, detail = _check_addresses_before_order(calls)
        assert ok, detail

    def test_order_before_addresses_fails(self):
        calls = [
            {"name": "place_order", "arguments": {"address_id": 1}},
            {"name": "view_saved_addresses", "arguments": {}},
        ]
        ok, detail = _check_addresses_before_order(calls)
        assert not ok
        assert "place_order was called before view_saved_addresses" in detail

    def test_no_addresses_call_fails(self):
        calls = [
            {"name": "view_cart", "arguments": {}},
            {"name": "place_order", "arguments": {"address_id": 1}},
        ]
        ok, detail = _check_addresses_before_order(calls)
        assert not ok
        assert "view_saved_addresses was not called" in detail

    def test_addresses_only_passes(self):
        calls = [{"name": "view_saved_addresses", "arguments": {}}]
        ok, detail = _check_addresses_before_order(calls)
        assert ok, detail
