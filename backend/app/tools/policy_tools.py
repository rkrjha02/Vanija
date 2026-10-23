from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.data.policies import search_chunks
from app.embeddings import embed_question


async def retrieve_policies(session: AsyncSession, question: str) -> dict:
    """Find the policy sections closest to a question.

    An EmbeddingError or database error is NOT caught here: the agent loop turns
    any tool error into a generic "something went wrong" result.
    """
    vector = await embed_question(question)
    chunks = await search_chunks(
        session,
        vector,
        limit=settings.policy_results_limit,
        min_similarity=settings.policy_min_similarity,
    )
    if not chunks:
        return {"status": "no_relevant_policy", "results": []}
    return {
        "status": "found",
        "results": [
            {"document_title": c["document_title"], "section": c["section"], "text": c["text"]}
            for c in chunks
        ],
    }


def validate_search_policies(args: dict) -> str | None:
    question = args.get("question")
    if not isinstance(question, str) or not question.strip():
        return "question is required: a short, self-contained policy question"
    if len(question) > settings.policy_question_max_length:
        return f"question must be at most {settings.policy_question_max_length} characters"
    return None


async def handle_search_policies(session: AsyncSession, args: dict, customer_id: str = "") -> dict:
    # Policies are the same for every customer, so customer_id is not used.
    return await retrieve_policies(session, args["question"].strip())


TOOL_HANDLERS = {
    "search_policies": {
        "validate": validate_search_policies,
        "handle": handle_search_policies,
    },
}
