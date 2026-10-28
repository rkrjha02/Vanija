"""Tests for the cards one chat turn returns. No database and no LLM calls."""

from app.agent.loop import _add_card, _build_card


def _cart_result(*names: str) -> dict:
    items = [
        {"product_id": f"P{i}", "name": name, "quantity": 1, "unit_price": 100.0,
         "line_total": 100.0, "problem": ""}
        for i, name in enumerate(names, start=1)
    ]
    return {"status": "success", "items": items, "cart_total": 100.0 * len(items), "has_problems": False}


def test_two_adds_in_one_turn_give_one_cart_card_with_both_items():
    cards = []
    _add_card(cards, _build_card("add_to_cart", _cart_result("Phone A")))
    _add_card(cards, _build_card("add_to_cart", _cart_result("Phone A", "Phone D")))

    assert len(cards) == 1
    assert [item["name"] for item in cards[0]["items"]] == ["Phone A", "Phone D"]
    assert cards[0]["cart_total"] == 200.0


def test_add_then_update_keeps_only_the_latest_cart():
    cards = []
    _add_card(cards, _build_card("add_to_cart", _cart_result("Phone A")))
    _add_card(cards, _build_card("update_cart_item", _cart_result("Phone A", "Phone B")))

    assert [c["type"] for c in cards] == ["cart"]
    assert len(cards[0]["items"]) == 2


def test_other_cards_stay_and_keep_their_order():
    products = {"type": "products", "items": [{"id": "PHN001"}]}
    cards = []
    _add_card(cards, products)
    _add_card(cards, _build_card("add_to_cart", _cart_result("Phone A")))
    _add_card(cards, _build_card("add_to_cart", _cart_result("Phone A", "Phone D")))

    assert [c["type"] for c in cards] == ["products", "cart"]
    assert cards[0] is products


def test_two_product_lists_in_one_turn_are_both_kept():
    cards = []
    _add_card(cards, {"type": "products", "items": [{"id": "PHN001"}]})
    _add_card(cards, {"type": "products", "items": [{"id": "LAP001"}]})

    assert len(cards) == 2
