"""Tests for reply_checker. Pure unit tests, no LLM or database calls."""

from tests.reply_checker import check_reply


class TestAmountChecks:
    def test_correct_amount_passes(self):
        result = check_reply(
            "Phone A costs ₹9,999.",
            ['{"status":"success","products":[{"id":"PHN001","name":"Phone A","price":9999}]}'],
            [],
        )
        assert result.status == "passed"
        assert len(result.passed) == 1

    def test_invented_amount_fails(self):
        result = check_reply(
            "Phone A costs ₹8,999.",
            ['{"status":"success","products":[{"id":"PHN001","name":"Phone A","price":9999}]}'],
            [],
        )
        assert result.status == "failed"
        assert "₹8,999" in result.failed[0]

    def test_rs_prefix(self):
        result = check_reply(
            "The price is Rs 9999.",
            ['{"price": 9999}'],
            [],
        )
        assert result.status == "passed"

    def test_rs_dot_prefix(self):
        result = check_reply(
            "The price is Rs. 14,999.",
            ['{"price": 14999}'],
            [],
        )
        assert result.status == "passed"

    def test_inr_prefix(self):
        result = check_reply(
            "Total: INR 45,999.",
            ['{"cart_total": 45999}'],
            [],
        )
        assert result.status == "passed"

    def test_comma_normalization(self):
        """12,500 and 12500 are the same amount."""
        result = check_reply(
            "The total is ₹12,500.",
            ['{"cart_total": 12500}'],
            [],
        )
        assert result.status == "passed"

    def test_decimal_normalization(self):
        """12500.00 and 12500 are the same amount."""
        result = check_reply(
            "The total is ₹12,500.00.",
            ['{"cart_total": 12500}'],
            [],
        )
        assert result.status == "passed"

    def test_multiple_amounts_mixed(self):
        result = check_reply(
            "Phone A is ₹9,999 and Phone B is ₹14,999. Total: ₹99,999.",
            ['{"products":[{"price":9999},{"price":14999}]}'],
            [],
        )
        assert result.status == "failed"
        assert len(result.passed) == 2
        assert len(result.failed) == 1

    def test_amount_from_state_block_is_unsourced(self):
        """Only this turn's tool results count. A price in the state block does not."""
        result = check_reply(
            "Phone A costs ₹9,999.",
            [],
            [],
        )
        assert result.status == "failed"


class TestDurationChecks:
    def test_correct_duration_passes(self):
        result = check_reply(
            "You have 7 days to return the product.",
            [],
            ["Returns are accepted within 7 days of delivery."],
        )
        assert result.status == "passed"

    def test_invented_duration_fails(self):
        result = check_reply(
            "You have 14 days to return the product.",
            [],
            ["Returns are accepted within 7 days of delivery."],
        )
        assert result.status == "failed"
        assert "14 days" in result.failed[0]

    def test_duration_singular_plural_match(self):
        """'1 month' and '1 months' normalize to the same thing."""
        result = check_reply(
            "The warranty is 12 months.",
            [],
            ["Phones have a 12 month warranty."],
        )
        assert result.status == "passed"

    def test_duration_from_tool_result(self):
        """Durations can also appear in tool results (e.g. battery hours)."""
        result = check_reply(
            "Battery lasts 30 hours.",
            ['{"specs":{"battery_hours":30},"description":"30 hours playback"}'],
            [],
        )
        assert result.status == "passed"

    def test_word_number_duration_needs_review(self):
        result = check_reply(
            "You have seven days to return the item.",
            [],
            ["Returns are accepted within 7 days of delivery."],
        )
        assert result.status == "needs_review"
        assert any("seven days" in s for s in result.needs_review)


class TestUserMessageAmounts:
    def test_amount_from_user_message_passes(self):
        """An amount the customer typed (e.g. 'under 15000') is not flagged."""
        result = check_reply(
            "Here are phones under ₹15,000.",
            ['{"products":[{"price":9999},{"price":14999}]}'],
            [],
            user_message="Show me phones under 15000",
        )
        assert result.status == "passed"
        assert "₹15,000" in result.passed_from_user

    def test_invented_amount_still_fails(self):
        """An amount in neither tool results nor user message is still flagged."""
        result = check_reply(
            "This phone costs ₹7,777.",
            ['{"products":[{"price":9999}]}'],
            [],
            user_message="Show me phones under 15000",
        )
        assert result.status == "failed"
        assert any("7,777" in a for a in result.failed)

    def test_amount_from_earlier_turn_not_accepted(self):
        """Only the current turn's user_message counts, not earlier history."""
        result = check_reply(
            "Here are phones under ₹15,000.",
            ['{"products":[{"price":9999}]}'],
            [],
            user_message="What about the warranty?",
        )
        assert result.status == "failed"
        assert any("15,000" in a for a in result.failed)

    def test_amount_without_user_message_still_fails(self):
        """When no user_message is passed, unsourced amounts still fail."""
        result = check_reply(
            "Here are phones under ₹15,000.",
            ['{"products":[{"price":9999}]}'],
            [],
        )
        assert result.status == "failed"
        assert any("15,000" in a for a in result.failed)


class TestEdgeCases:
    def test_no_amounts_or_durations(self):
        result = check_reply(
            "Hello! How can I help you today?",
            [],
            [],
        )
        assert result.status == "passed"
        assert len(result.passed) == 0

    def test_amount_in_cart_total(self):
        """The cart total computed by the backend is a valid source."""
        result = check_reply(
            "Your cart total is ₹29,998.",
            ['{"status":"success","items":[{"line_total":29998}],"cart_total":29998}'],
            [],
        )
        assert result.status == "passed"
