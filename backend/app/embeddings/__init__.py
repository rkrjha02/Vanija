"""Embedding layer. Only this folder talks to an embedding API."""

from app.config import settings
from app.embeddings import gemini
from app.embeddings.errors import EmbeddingError

_PROVIDERS = {"gemini": gemini}


def _provider():
    provider = _PROVIDERS.get(settings.embedding_provider)
    if provider is None:
        raise EmbeddingError(f"Unknown embedding provider: {settings.embedding_provider}")
    return provider


async def embed_documents(items: list[tuple[str, str]]) -> list[list[float]]:
    """Embed policy chunks. Each item is (document title, chunk text)."""
    return await _provider().embed_documents(items)


async def embed_question(question: str) -> list[float]:
    """Embed a customer's question for searching the policy chunks."""
    return await _provider().embed_question(question)


__all__ = ["EmbeddingError", "embed_documents", "embed_question"]
