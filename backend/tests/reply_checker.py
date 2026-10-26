"""Check that amounts and durations in a reply are sourced from tool results or policy text."""

import re

AMOUNT_RE = re.compile(
    r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)", re.IGNORECASE
)

DURATION_RE = re.compile(
    r"(\d+)\s*(days?|weeks?|months?|years?|hours?)", re.IGNORECASE
)

WORD_NUMBER_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)\b",
    re.IGNORECASE,
)

WORD_DURATION_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)"
    r"\s+(days?|weeks?|months?|years?|hours?)\b",
    re.IGNORECASE,
)


def _normalize_amount(raw: str) -> str:
    """Remove commas and trailing .00 so 12,500 = 12500 = 12500.00."""
    n = raw.replace(",", "")
    if "." in n:
        n = n.rstrip("0").rstrip(".")
    return n


def _normalize_duration(number: str, unit: str) -> str:
    """Normalize to singular unit: '7 days' -> '7 day'."""
    unit = unit.lower().rstrip("s")
    return f"{number} {unit}"


def _extract_amounts(text: str) -> list[str]:
    """Extract all ₹/Rs/INR amounts, normalized (no commas, no trailing zeros)."""
    return [_normalize_amount(m.group(1)) for m in AMOUNT_RE.finditer(text)]


def _extract_durations(text: str) -> list[str]:
    """Extract all numeric durations, normalized to singular unit."""
    return [_normalize_duration(m.group(1), m.group(2)) for m in DURATION_RE.finditer(text)]


def _has_word_durations(text: str) -> bool:
    """Check if the text has durations written as words (e.g. 'seven days')."""
    return bool(WORD_DURATION_RE.search(text))


def _build_source_text(tool_results: list[str], policy_texts: list[str]) -> str:
    """Combine all source texts for searching. Only this turn's sources count."""
    return "\n".join(tool_results + policy_texts)


class CheckResult:
    def __init__(self):
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.needs_review: list[str] = []
        self.passed_from_user: list[str] = []

    @property
    def status(self) -> str:
        if self.failed:
            return "failed"
        if self.needs_review:
            return "needs_review"
        return "passed"


def check_reply(
    reply: str,
    tool_results: list[str],
    policy_texts: list[str],
    user_message: str = "",
) -> CheckResult:
    """Check amounts and durations in reply against this turn's sources.

    Args:
        reply: The LLM's final reply text.
        tool_results: JSON strings from each tool call in this turn.
        policy_texts: Text from policy chunks returned in this turn.
        user_message: The customer's message for this turn only.

    Returns:
        CheckResult with passed/failed/needs_review/passed_from_user lists.
    """
    result = CheckResult()
    source = _build_source_text(tool_results, policy_texts)
    source_amounts = set(_extract_amounts(source))
    source_durations = set(_extract_durations(source))

    # Also extract raw numbers from source for matching amounts that appear
    # without a currency prefix in the source (e.g. "price": 9999 in JSON).
    source_numbers = set(re.findall(r"\b(\d[\d,]*(?:\.\d+)?)\b", source))
    source_numbers_normalized = {_normalize_amount(n) for n in source_numbers}

    # Amounts from the customer's current-turn message are a valid source.
    user_amounts = set(_extract_amounts(user_message))
    user_numbers = set(re.findall(r"\b(\d[\d,]*(?:\.\d+)?)\b", user_message))
    user_numbers_normalized = {_normalize_amount(n) for n in user_numbers}

    for m in AMOUNT_RE.finditer(reply):
        raw = m.group(0)
        normalized = _normalize_amount(m.group(1))
        if normalized in source_amounts or normalized in source_numbers_normalized:
            result.passed.append(raw)
        elif normalized in user_amounts or normalized in user_numbers_normalized:
            result.passed_from_user.append(raw)
        else:
            result.failed.append(raw)

    for m in DURATION_RE.finditer(reply):
        raw = m.group(0)
        normalized = _normalize_duration(m.group(1), m.group(2))
        if normalized in source_durations:
            result.passed.append(raw)
        else:
            result.failed.append(raw)

    if _has_word_durations(reply):
        for m in WORD_DURATION_RE.finditer(reply):
            result.needs_review.append(m.group(0))

    return result
