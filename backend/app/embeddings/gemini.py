import logging

from google import genai
from google.genai import types

from app.config import settings
from app.embeddings.errors import EmbeddingError

logger = logging.getLogger(__name__)

# Gemini accepts at most 100 texts in one embedding request.
MAX_TEXTS_PER_REQUEST = 100

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise EmbeddingError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def embed_documents(items: list[tuple[str, str]]) -> list[list[float]]:
    # gemini-embedding-2 has no task_type; the task is written at the start of the text.
    texts = [f"title: {title} | text: {text}" for title, text in items]
    return await _embed(texts)


async def embed_question(question: str) -> list[float]:
    vectors = await _embed([f"task: search result | query: {question}"])
    return vectors[0]


async def _embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if len(texts) > MAX_TEXTS_PER_REQUEST:
        raise EmbeddingError(f"At most {MAX_TEXTS_PER_REQUEST} texts per request")

    # One Content per text, so Gemini returns one vector per text (not one combined vector).
    contents = [types.Content(parts=[types.Part(text=text)]) for text in texts]
    try:
        response = await _get_client().aio.models.embed_content(
            model=settings.embedding_model,
            contents=contents,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.embedding_dimensions,
            ),
        )
    except EmbeddingError:
        raise
    except Exception as exc:
        logger.exception("Embedding request failed")
        raise EmbeddingError("Embedding request failed") from exc

    vectors = [list(embedding.values or []) for embedding in response.embeddings or []]
    if len(vectors) != len(texts):
        raise EmbeddingError(f"Expected {len(texts)} vectors, got {len(vectors)}")
    for vector in vectors:
        if len(vector) != settings.embedding_dimensions:
            raise EmbeddingError(
                f"Expected {settings.embedding_dimensions} numbers, got {len(vector)}"
            )
    return vectors
