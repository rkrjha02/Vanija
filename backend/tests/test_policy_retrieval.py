"""Tests for policy retrieval with hand-made vectors. No real API calls."""

import pytest
from sqlalchemy import delete

import app.tools.policy_tools as policy_mod
from app.config import settings
from app.data.models import PolicyDocument
from app.data.policies import replace_document, search_chunks
from app.embeddings import EmbeddingError
from app.tools.policy_tools import retrieve_policies

DIMS = settings.embedding_dimensions


def axis(*weights):
    """A vector with the given numbers at the start and zeros after."""
    return list(weights) + [0.0] * (DIMS - len(weights))


@pytest.fixture
async def policies(session):
    await session.execute(delete(PolicyDocument))
    await session.commit()
    await replace_document(session, "returns.md", "Returns Policy", "h1", [
        {"section": "Headphones", "chunk_text": "Returns Policy > Headphones: Unopened: 7 days.",
         "embedding": axis(1, 0)},                                   # A
        {"section": "Laptops", "chunk_text": "Returns Policy > Laptops: 10 days.",
         "embedding": axis(0, 1)},                                   # B
    ])
    await replace_document(session, "warranty.md", "Warranty Policy", "h2", [
        {"section": "Headphones", "chunk_text": "Warranty Policy > Headphones: 6 months.",
         "embedding": axis(0.8, 0.6)},                               # C
    ])
    yield session
    await session.execute(delete(PolicyDocument))
    await session.commit()


@pytest.fixture
def question_vector(monkeypatch):
    def install(vector=None, error=None):
        async def fake_embed_question(question):
            if error:
                raise error
            return vector
        monkeypatch.setattr(policy_mod, "embed_question", fake_embed_question)
    return install


async def test_search_orders_by_similarity_and_drops_low_scores(policies):
    results = await search_chunks(policies, axis(1, 0), limit=3, min_similarity=0.5)

    assert [(r["source_file"], r["section"]) for r in results] == [
        ("returns.md", "Headphones"), ("warranty.md", "Headphones")]
    assert results[0]["similarity"] == pytest.approx(1.0)
    assert results[1]["similarity"] == pytest.approx(0.8)


async def test_search_respects_limit(policies):
    results = await search_chunks(policies, axis(1, 0), limit=1, min_similarity=0.0)
    assert len(results) == 1


async def test_search_text_has_prefix_removed(policies):
    [top] = await search_chunks(policies, axis(1, 0), limit=1, min_similarity=0.5)
    assert top["text"] == "Unopened: 7 days."
    assert top["document_title"] == "Returns Policy"


async def test_retrieve_found_returns_only_title_section_text(policies, question_vector):
    question_vector(axis(1, 0))

    result = await retrieve_policies(policies, "Can I return opened headphones?")

    assert result["status"] == "found"
    assert result["results"][0] == {"document_title": "Returns Policy",
                                    "section": "Headphones", "text": "Unopened: 7 days."}
    assert len(result["results"]) <= settings.policy_results_limit


async def test_retrieve_nothing_close_enough(policies, question_vector):
    question_vector(axis(0, 0, 1))  # points away from every chunk

    result = await retrieve_policies(policies, "Do you recycle old batteries?")

    assert result == {"status": "no_relevant_policy", "results": []}


async def test_retrieve_embedding_failure_is_raised_for_the_loop(policies, question_vector):
    question_vector(error=EmbeddingError("quota"))
    with pytest.raises(EmbeddingError):
        await retrieve_policies(policies, "warranty?")
