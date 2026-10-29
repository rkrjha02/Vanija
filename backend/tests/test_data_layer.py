import pytest

from app.config import settings
from app.data.customers import create_customer, get_customer
from app.data.products import get_categories, get_product_details, search_products
from app.data.conversations import get_or_create_conversation, update_shown_products
from app.data.messages import get_history_page, get_recent_messages, get_turn_messages, save_message

_TEST_EMBEDDING = [0.1] * settings.embedding_dimensions


class TestCustomers:
    async def test_create_and_get(self, session):
        cid = await create_customer(session)
        assert len(cid) > 20
        customer = await get_customer(session, cid)
        assert customer is not None
        assert customer["id"] == cid

    async def test_get_nonexistent(self, session):
        result = await get_customer(session, "does-not-exist")
        assert result is None


class TestProducts:
    async def test_get_categories(self, seeded_session):
        cats = await get_categories(seeded_session)
        assert "phone" in cats
        assert "laptop" in cats
        assert "headphone" in cats

    async def test_search_by_category(self, seeded_session):
        result = await search_products(
            seeded_session, query_embedding=_TEST_EMBEDDING, category="phone"
        )
        assert result["total_matches"] >= 2
        for p in result["products"]:
            assert p["category"] == "phone"

    async def test_search_max_price(self, seeded_session):
        result = await search_products(
            seeded_session, query_embedding=_TEST_EMBEDDING,
            category="phone", max_price=10000,
        )
        for p in result["products"]:
            assert p["price"] <= 10000

    async def test_search_brand(self, seeded_session):
        result = await search_products(
            seeded_session, query_embedding=_TEST_EMBEDDING,
            category="phone", brand="Samsung",
        )
        for p in result["products"]:
            assert p["brand"].lower() == "samsung"

    async def test_search_excludes_inactive(self, seeded_session):
        result = await search_products(
            seeded_session, query_embedding=_TEST_EMBEDDING, category="phone"
        )
        ids = [p["id"] for p in result["products"]]
        assert "PHN099" not in ids

    async def test_search_no_match(self, seeded_session):
        result = await search_products(
            seeded_session, query_embedding=_TEST_EMBEDDING,
            category="phone", max_price=1,
        )
        assert result["total_matches"] == 0
        assert result["products"] == []

    async def test_search_without_category(self, seeded_session):
        result = await search_products(
            seeded_session, query_embedding=_TEST_EMBEDDING
        )
        categories = {p["category"] for p in result["products"]}
        assert len(categories) > 1

    async def test_search_limit(self, seeded_session):
        result = await search_products(
            seeded_session, query_embedding=_TEST_EMBEDDING, limit=1
        )
        assert len(result["products"]) == 1

    async def test_get_details(self, seeded_session):
        details = await get_product_details(seeded_session, ["PHN001"])
        assert len(details) == 1
        assert details[0]["id"] == "PHN001"
        assert "description" in details[0]
        assert "specs" in details[0]

    async def test_get_details_not_found(self, seeded_session):
        details = await get_product_details(seeded_session, ["FAKE999"])
        assert details[0]["status"] == "not_found"

    async def test_get_details_inactive(self, seeded_session):
        details = await get_product_details(seeded_session, ["PHN099"])
        assert details[0]["status"] == "not_found"

    async def test_get_details_mixed(self, seeded_session):
        details = await get_product_details(
            seeded_session, ["PHN001", "FAKE999"]
        )
        assert details[0]["id"] == "PHN001"
        assert details[1]["status"] == "not_found"


class TestConversations:
    async def test_create_conversation(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)
        assert conv["customer_id"] == cid
        assert conv["shown_products"] == []

    async def test_get_existing_conversation(self, session):
        cid = await create_customer(session)
        conv1 = await get_or_create_conversation(session, cid)
        conv2 = await get_or_create_conversation(session, cid)
        assert conv1["id"] == conv2["id"]

    async def test_update_shown_products(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)
        new_state = [{"label": "phones", "products": [{"position": 1, "id": "PHN001", "name": "Phone A"}]}]
        await update_shown_products(session, conv["id"], new_state)
        conv2 = await get_or_create_conversation(session, cid)
        assert len(conv2["shown_products"]) == 1
        assert conv2["shown_products"][0]["label"] == "phones"


class TestMessages:
    async def test_save_and_get_recent(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)

        await save_message(session, conv["id"], "turn-1", "user", content="Hello")
        await save_message(session, conv["id"], "turn-1", "assistant", content="Hi there!")

        recent = await get_recent_messages(session, conv["id"], limit=10)
        assert len(recent) == 2
        assert recent[0]["role"] == "user"
        assert recent[1]["role"] == "assistant"

    async def test_recent_excludes_tool_messages(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)

        await save_message(session, conv["id"], "turn-1", "user", content="Search phones")
        await save_message(session, conv["id"], "turn-1", "assistant",
                           content=None, tool_calls=[{"id": "tc1", "name": "search", "arguments": {}}])
        await save_message(session, conv["id"], "turn-1", "tool",
                           content='{"status": "success"}', tool_call_id="tc1")
        await save_message(session, conv["id"], "turn-1", "assistant", content="Here are the results")

        recent = await get_recent_messages(session, conv["id"], limit=10)
        roles = [m["role"] for m in recent]
        assert "tool" not in roles
        assert len(recent) == 2

    async def test_history_page_returns_newest_messages_oldest_first(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)
        for i in range(1, 8):
            await save_message(session, conv["id"], f"turn-{i}", "user", content=f"m{i}")

        page = await get_history_page(session, conv["id"], before_id=None, limit=3)
        assert [m["content"] for m in page["messages"]] == ["m5", "m6", "m7"]
        assert page["has_more"] is True
        assert all("id" in m for m in page["messages"])

    async def test_history_pages_join_without_gaps_or_overlap(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)
        for i in range(1, 8):
            await save_message(session, conv["id"], f"turn-{i}", "user", content=f"m{i}")

        seen = []
        before = None
        while True:
            page = await get_history_page(session, conv["id"], before_id=before, limit=3)
            seen = [m["content"] for m in page["messages"]] + seen
            if not page["has_more"]:
                break
            before = page["messages"][0]["id"]

        assert seen == [f"m{i}" for i in range(1, 8)]

    async def test_history_page_shows_only_customer_text_and_final_replies(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)

        await save_message(session, conv["id"], "turn-1", "user", content="Search phones")
        await save_message(session, conv["id"], "turn-1", "assistant", content="Let me check.",
                           tool_calls=[{"id": "tc1", "name": "search_products", "arguments": {}}])
        await save_message(session, conv["id"], "turn-1", "tool",
                           content='{"status": "success"}', tool_call_id="tc1")
        await save_message(session, conv["id"], "turn-1", "assistant", content="")
        await save_message(session, conv["id"], "turn-1", "assistant", content="Here are the results")

        page = await get_history_page(session, conv["id"], before_id=None, limit=50)
        assert [m["content"] for m in page["messages"]] == ["Search phones", "Here are the results"]
        assert page["has_more"] is False

    async def test_history_page_for_empty_conversation(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)
        page = await get_history_page(session, conv["id"], before_id=None, limit=50)
        assert page == {"messages": [], "has_more": False}

    async def test_history_page_never_returns_another_conversation(self, session):
        cid_a = await create_customer(session)
        conv_a = await get_or_create_conversation(session, cid_a)
        cid_b = await create_customer(session)
        conv_b = await get_or_create_conversation(session, cid_b)
        await save_message(session, conv_a["id"], "turn-1", "user", content="A's secret")
        await save_message(session, conv_b["id"], "turn-1", "user", content="B's message")

        page = await get_history_page(session, conv_b["id"], before_id=10**9, limit=50)
        assert [m["content"] for m in page["messages"]] == ["B's message"]

    async def test_get_turn_messages(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)

        await save_message(session, conv["id"], "turn-1", "user", content="Hi")
        await save_message(session, conv["id"], "turn-1", "assistant", content="Hello")
        await save_message(session, conv["id"], "turn-2", "user", content="Other turn")

        turn_msgs = await get_turn_messages(session, conv["id"], "turn-1")
        assert len(turn_msgs) == 2
        assert all(m["role"] in ("user", "assistant") for m in turn_msgs)

    async def test_history_returns_cards_with_assistant_message(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)
        sample_cards = [{"type": "products", "items": [{"id": "PHN001", "name": "Phone A"}]}]

        await save_message(session, conv["id"], "turn-1", "user", content="Show phones")
        await save_message(session, conv["id"], "turn-1", "assistant", content="Here you go", cards=sample_cards)

        page = await get_history_page(session, conv["id"], before_id=None, limit=50)
        msgs = page["messages"]
        assert len(msgs) == 2
        assert msgs[0]["cards"] is None
        assert msgs[1]["cards"] == sample_cards

    async def test_history_returns_null_cards_when_none(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)

        await save_message(session, conv["id"], "turn-1", "user", content="Hello")
        await save_message(session, conv["id"], "turn-1", "assistant", content="Hi there!")

        page = await get_history_page(session, conv["id"], before_id=None, limit=50)
        for msg in page["messages"]:
            assert msg["cards"] is None

    async def test_history_empty_cards_list_stored_as_null(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)

        await save_message(session, conv["id"], "turn-1", "assistant", content="No cards", cards=[])

        page = await get_history_page(session, conv["id"], before_id=None, limit=50)
        assert page["messages"][0]["cards"] is None

    async def test_cards_survive_pagination(self, session):
        cid = await create_customer(session)
        conv = await get_or_create_conversation(session, cid)
        cards_a = [{"type": "products", "items": [{"id": "A"}]}]
        cards_b = [{"type": "cart", "items": [], "cart_total": 100, "has_problems": False}]

        await save_message(session, conv["id"], "turn-1", "user", content="m1")
        await save_message(session, conv["id"], "turn-1", "assistant", content="r1", cards=cards_a)
        await save_message(session, conv["id"], "turn-2", "user", content="m2")
        await save_message(session, conv["id"], "turn-2", "assistant", content="r2", cards=cards_b)

        page1 = await get_history_page(session, conv["id"], before_id=None, limit=2)
        assert page1["has_more"] is True
        assert page1["messages"][1]["cards"] == cards_b

        before = page1["messages"][0]["id"]
        page2 = await get_history_page(session, conv["id"], before_id=before, limit=2)
        assert page2["messages"][1]["cards"] == cards_a
