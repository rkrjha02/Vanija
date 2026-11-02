"""Tests for product search pagination (offset, total_count, last_search_context, state block)."""

import pytest
from unittest.mock import AsyncMock, patch

from app.agent.state_block import format_state_block
from app.data.conversations import (
    get_or_create_conversation,
    update_last_search_context,
)
from app.data.models import Conversation, Customer
from app.data.products import search_products as db_search_products


_TEST_EMBEDDING = [0.1] * 768


@pytest.fixture
async def customer_with_conversation(seeded_session):
    """Create a customer and conversation for testing."""
    session = seeded_session
    customer = Customer(id="PAGING_CUST_001", user_id="PAGING_USER_001", name="Pager")
    from app.data.models import User
    user = User(id="PAGING_USER_001", email="pager@test.com", name="Pager", auth_provider="email", password_hash="x")
    await session.merge(user)
    await session.merge(customer)
    await session.commit()
    conv = await get_or_create_conversation(session, "PAGING_CUST_001")
    return session, conv


# --- Test 1: search with offset=0 returns total_count and products ---

@pytest.mark.asyncio
async def test_search_offset_zero_returns_total_count(seeded_session):
    """search_products with offset=0 returns total_count and products."""
    result = await db_search_products(
        session=seeded_session,
        query_embedding=_TEST_EMBEDDING,
        limit=2,
        offset=0,
    )
    assert "total_count" in result
    assert isinstance(result["total_count"], int)
    assert result["total_count"] >= len(result["products"])
    assert len(result["products"]) <= 2
    for p in result["products"]:
        assert "position" in p


# --- Test 2: search with offset=5 returns the next batch ---

@pytest.mark.asyncio
async def test_search_with_offset_returns_next_batch(seeded_session):
    """search_products with offset skips earlier results."""
    all_results = await db_search_products(
        session=seeded_session,
        query_embedding=_TEST_EMBEDDING,
        limit=10,
        offset=0,
    )
    total = all_results["total_count"]

    if total <= 2:
        pytest.skip("Not enough products to test offset pagination")

    first_page = await db_search_products(
        session=seeded_session,
        query_embedding=_TEST_EMBEDDING,
        limit=2,
        offset=0,
    )
    second_page = await db_search_products(
        session=seeded_session,
        query_embedding=_TEST_EMBEDDING,
        limit=2,
        offset=2,
    )

    first_ids = {p["id"] for p in first_page["products"]}
    second_ids = {p["id"] for p in second_page["products"]}
    assert first_ids.isdisjoint(second_ids), "Pages should not overlap"

    assert second_page["total_count"] == first_page["total_count"]

    if second_page["products"]:
        assert second_page["products"][0]["position"] == 3


# --- Test 3: last_search_context is saved to conversations table ---

@pytest.mark.asyncio
async def test_last_search_context_saved(customer_with_conversation):
    """update_last_search_context saves context to the conversation."""
    session, conv = customer_with_conversation

    context = {
        "query": "wireless headphones",
        "offset": 0,
        "total_count": 12,
        "filters": {"category": "headphone"},
    }
    await update_last_search_context(session, conv["id"], context)

    updated = await get_or_create_conversation(session, conv["customer_id"])
    assert updated["last_search_context"] is not None
    assert updated["last_search_context"]["query"] == "wireless headphones"
    assert updated["last_search_context"]["total_count"] == 12
    assert updated["last_search_context"]["offset"] == 0
    assert updated["last_search_context"]["filters"]["category"] == "headphone"


# --- Test 4: State block includes last search context line ---

def test_state_block_includes_search_context():
    """format_state_block includes the last search context line when present."""
    shown = [
        {
            "label": "phones under ₹15,000",
            "products": [
                {"position": 1, "id": "PHN001", "name": "Phone A"},
                {"position": 2, "id": "PHN002", "name": "Phone B"},
            ],
        }
    ]
    context = {
        "query": "budget phones",
        "offset": 0,
        "total_count": 8,
        "filters": {"category": "phone", "max_price": 15000},
    }
    text = format_state_block(shown, last_search_context=context)
    assert "Last product search:" in text
    assert "query='budget phones'" in text
    assert "showed results 1-5 of 8 total" in text
    assert "category=phone" in text
    assert "max_price=15000" in text
    assert "The customer can ask to see more." in text
    assert "Latest list" in text


# --- Test 5: State block omits search context when NULL ---

def test_state_block_omits_search_context_when_null():
    """format_state_block does not include search context line when it is None."""
    shown = [
        {
            "label": "laptops",
            "products": [
                {"position": 1, "id": "LAP001", "name": "Laptop A"},
            ],
        }
    ]
    text = format_state_block(shown, last_search_context=None)
    assert "Last product search:" not in text
    assert "Latest list (laptops):" in text


def test_state_block_empty_with_no_products_no_context():
    """format_state_block returns empty string with no products and no context."""
    assert format_state_block([], last_search_context=None) == ""


def test_state_block_search_context_with_offset():
    """State block shows correct range when offset > 0."""
    context = {
        "query": "laptops",
        "offset": 5,
        "total_count": 12,
        "filters": {},
    }
    text = format_state_block([], last_search_context=context)
    assert "showed results 6-10 of 12 total" in text
    assert "Filters:" not in text
