"""Tests for the embedding layer. The Gemini client is faked; no real API calls."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

import app.embeddings.gemini as gemini_mod
from app.config import settings
from app.data.models import PolicyChunk, PolicyDocument
from app.embeddings import EmbeddingError, embed_documents, embed_question

DIMS = settings.embedding_dimensions


def _fake_client(vectors=None, error=None):
    embed = AsyncMock()
    if error:
        embed.side_effect = error
    else:
        embed.return_value = SimpleNamespace(
            embeddings=[SimpleNamespace(values=v) for v in vectors]
        )
    return SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(embed_content=embed))), embed


def _sent_texts(embed_mock):
    contents = embed_mock.call_args.kwargs["contents"]
    return [content.parts[0].text for content in contents]


@pytest.fixture
def fake(monkeypatch):
    def install(vectors=None, error=None):
        client, embed = _fake_client(vectors, error)
        monkeypatch.setattr(gemini_mod, "_get_client", lambda: client)
        return embed
    return install


async def test_documents_get_one_vector_each_with_document_prefix(fake):
    embed = fake([[0.1] * DIMS, [0.2] * DIMS])

    vectors = await embed_documents([("Warranty Policy", "Phones: 12 months"),
                                     ("Returns Policy", "Laptops: 10 days")])

    assert len(vectors) == 2 and len(vectors[0]) == DIMS
    assert _sent_texts(embed) == ["title: Warranty Policy | text: Phones: 12 months",
                                  "title: Returns Policy | text: Laptops: 10 days"]
    call = embed.call_args.kwargs
    assert call["model"] == settings.embedding_model
    assert call["config"].output_dimensionality == DIMS


async def test_question_gets_query_prefix(fake):
    embed = fake([[0.3] * DIMS])

    vector = await embed_question("Can I return opened headphones?")

    assert len(vector) == DIMS
    assert _sent_texts(embed) == ["task: search result | query: Can I return opened headphones?"]


async def test_wrong_vector_size_raises(fake):
    fake([[0.1] * 10])
    with pytest.raises(EmbeddingError):
        await embed_question("warranty?")


async def test_wrong_vector_count_raises(fake):
    fake([[0.1] * DIMS])
    with pytest.raises(EmbeddingError):
        await embed_documents([("A", "one"), ("B", "two")])


async def test_api_failure_becomes_embedding_error(fake):
    fake(error=RuntimeError("network down"))
    with pytest.raises(EmbeddingError):
        await embed_question("warranty?")


async def test_missing_api_key_raises(monkeypatch):
    monkeypatch.setattr(gemini_mod, "_client", None)
    monkeypatch.setattr(settings, "gemini_api_key", "")
    with pytest.raises(EmbeddingError):
        await embed_question("warranty?")


async def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "embedding_provider", "nobody")
    with pytest.raises(EmbeddingError):
        await embed_question("warranty?")


async def test_too_many_texts_raises(fake):
    fake([])
    with pytest.raises(EmbeddingError):
        await embed_documents([("T", "x")] * (gemini_mod.MAX_TEXTS_PER_REQUEST + 1))


async def test_vector_can_be_stored_and_read_back(session):
    document = PolicyDocument(title="Test Policy", source_file="test_store.md", content_hash="abc")
    session.add(document)
    await session.flush()
    session.add(PolicyChunk(document_id=document.id, chunk_index=0, section="Phones",
                            chunk_text="Test Policy > Phones: text", embedding=[0.5] * DIMS))
    await session.flush()

    stored = (await session.execute(
        select(PolicyChunk.embedding).where(PolicyChunk.document_id == document.id)
    )).scalar_one()

    assert len(stored) == DIMS
    assert float(stored[0]) == pytest.approx(0.5)
