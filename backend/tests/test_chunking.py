"""Tests for splitting policy files into chunks (no database, no API)."""

import pytest

from app.config import settings
from app.ingest.chunking import build_chunks, content_hash

SAMPLE = """# Warranty Policy

> MADE-UP EXAMPLE for testing this project.

## Phones
Phones have a 12-month warranty. Water damage is not covered.

## Empty section

## Laptops
Laptops have a 12-month warranty.

### Batteries
Batteries are covered for 6 months.
"""


def test_title_and_one_chunk_per_section_with_prefix():
    title, chunks = build_chunks(SAMPLE, max_chars=1500)

    assert title == "Warranty Policy"
    assert [c.section for c in chunks] == ["Phones", "Laptops"]
    assert chunks[0].text == ("Warranty Policy > Phones: Phones have a 12-month warranty. "
                              "Water damage is not covered.")


def test_note_before_first_section_is_not_stored():
    _, chunks = build_chunks(SAMPLE, max_chars=1500)
    assert all("MADE-UP" not in c.text for c in chunks)


def test_subheadings_stay_inside_their_section():
    _, chunks = build_chunks(SAMPLE, max_chars=1500)
    assert "### Batteries" in chunks[1].text


def test_long_section_split_by_paragraph_keeps_prefix():
    paragraphs = [f"Paragraph {i} " + "word " * 40 for i in range(4)]
    markdown = "# Returns Policy\n\n## Phones\n" + "\n\n".join(paragraphs)

    _, chunks = build_chunks(markdown, max_chars=500)

    assert len(chunks) > 1
    assert all(c.text.startswith("Returns Policy > Phones: ") for c in chunks)
    assert all(len(c.text) <= 500 for c in chunks)
    assert "Paragraph 0" in chunks[0].text and "Paragraph 3" in chunks[-1].text


def test_windows_line_endings_work():
    title, chunks = build_chunks(SAMPLE.replace("\n", "\r\n"), max_chars=1500)
    assert title == "Warranty Policy" and len(chunks) == 2


def test_missing_title_raises():
    with pytest.raises(ValueError):
        build_chunks("## Phones\nText", max_chars=1500)


def test_hash_ignores_line_endings_but_not_content():
    assert content_hash("a\nb") == content_hash("a\r\nb")
    assert content_hash("7 days") != content_hash("10 days")


@pytest.mark.parametrize("name, sections", [
    ("returns.md", 6), ("warranty.md", 5), ("shipping.md", 6),
    ("cancellation.md", 4), ("cod.md", 5),
])
def test_real_policy_files_parse(name, sections):
    text = (settings.policies_dir / name).read_text(encoding="utf-8")
    title, chunks = build_chunks(text, settings.max_chunk_chars)
    assert title.endswith("Policy")
    assert len(chunks) == sections
