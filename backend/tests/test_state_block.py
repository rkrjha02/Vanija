from app.agent.state_block import format_state_block, update_state_block


def _make_products(count, prefix="PHN"):
    return [
        {"position": i + 1, "id": f"{prefix}{i:03d}", "name": f"Product {i}"}
        for i in range(count)
    ]


def test_add_first_list():
    products = _make_products(3)
    result = update_state_block([], products, "phones under 15000")
    assert len(result) == 1
    assert result[0]["label"] == "phones under 15000"
    assert len(result[0]["products"]) == 3


def test_newest_first():
    state = update_state_block([], _make_products(2, "PHN"), "phones")
    state = update_state_block(state, _make_products(2, "LAP"), "laptops")
    assert state[0]["label"] == "laptops"
    assert state[1]["label"] == "phones"


def test_max_three_lists():
    state = []
    for i in range(4):
        state = update_state_block(state, _make_products(2), f"list {i}")
    assert len(state) == 3
    assert state[0]["label"] == "list 3"


def test_product_cap_drops_oldest_list():
    state = update_state_block([], _make_products(6, "A"), "big list")
    state = update_state_block(state, _make_products(6, "B"), "second list")
    total = sum(len(lst["products"]) for lst in state)
    assert total <= 10
    assert state[0]["label"] == "second list"


def test_format_empty():
    assert format_state_block([]) == ""


def test_format_two_lists():
    state = update_state_block([], _make_products(2, "PHN"), "phones")
    state = update_state_block(state, _make_products(2, "LAP"), "laptops")
    text = format_state_block(state)
    assert "Latest list (laptops):" in text
    assert "Earlier list (phones):" in text
    assert "LAP000" in text
    assert "PHN000" in text
