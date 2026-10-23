"""Tests for tool 9, search_policies. No real API calls."""

import app.tools.policy_tools as policy_mod
from app.agent.loop import _build_card
from app.agent.validation import validate_tool_call
from app.config import settings
from app.tools.definitions import get_tool_definitions
from app.tools.registry import ALL_HANDLERS


def test_there_are_nine_tools_and_each_has_a_handler():
    names = [t["function"]["name"] for t in get_tool_definitions()]
    assert len(names) == 9
    assert "search_policies" in names
    assert set(names) == set(ALL_HANDLERS)


def test_question_is_required():
    definition = next(t for t in get_tool_definitions()
                      if t["function"]["name"] == "search_policies")
    assert definition["function"]["parameters"]["required"] == ["question"]


def test_valid_question_passes_and_customer_id_is_removed():
    args, error = validate_tool_call(
        "search_policies", {"question": "Can I return opened headphones?", "customer_id": "x"})
    assert error is None
    assert args == {"question": "Can I return opened headphones?"}


def test_missing_question_is_rejected():
    _, error = validate_tool_call("search_policies", {})
    assert "question is required" in error


def test_blank_question_is_rejected():
    _, error = validate_tool_call("search_policies", {"question": "   "})
    assert "question is required" in error


def test_non_text_question_is_rejected():
    _, error = validate_tool_call("search_policies", {"question": 42})
    assert "question is required" in error


def test_too_long_question_is_rejected():
    _, error = validate_tool_call(
        "search_policies", {"question": "a" * (settings.policy_question_max_length + 1)})
    assert str(settings.policy_question_max_length) in error


def test_no_card_is_built_for_policy_results():
    result = {"status": "found", "results": [
        {"document_title": "Returns Policy", "section": "Headphones", "text": "7 days."}]}
    assert _build_card("search_policies", result) is None


async def test_handler_passes_the_trimmed_question(monkeypatch):
    seen = {}

    async def fake_retrieve(session, question):
        seen["question"] = question
        return {"status": "no_relevant_policy", "results": []}
    monkeypatch.setattr(policy_mod, "retrieve_policies", fake_retrieve)

    result = await policy_mod.handle_search_policies(
        None, {"question": "  warranty for phones?  "}, customer_id="cust-1")

    assert seen["question"] == "warranty for phones?"
    assert result["status"] == "no_relevant_policy"
