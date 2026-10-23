"""Retrieval test set: REAL Gemini embedding calls (one per question), no chat LLM.

Uses the DEV database, so run `python -m app.ingest` first.
Run from backend/:  python tests/policy_retrieval_set.py
Used to tune POLICY_MIN_SIMILARITY in config.py.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.data.database import async_session, engine  # noqa: E402
from app.data.policies import search_chunks  # noqa: E402
from app.embeddings import embed_question  # noqa: E402
from app.ingest.ingest import _Pacer  # noqa: E402

# (question, kind, accepted answers as (file, section); empty = no answer exists)
CASES = [
    ("Can I return opened headphones?", "clear",
     [("returns.md", "Headphones")]),
    ("Is water damage covered for phones?", "clear",
     [("warranty.md", "Phones")]),
    ("How many days do I have to send back a faulty laptop?", "different wording",
     [("returns.md", "Laptops")]),
    ("How long until my parcel reaches a small town?", "different wording",
     [("shipping.md", "Delivery time")]),
    ("Can I pay by card when the delivery guy comes?", "different wording",
     [("cod.md", "Paying at the door")]),
    ("What happens if nobody is home for the delivery?", "different wording",
     [("shipping.md", "Failed delivery")]),
    ("Can I cancel after my order has been shipped?", "clear",
     [("cancellation.md", "Cancelling after the order ships")]),
    ("When will I get my refund?", "clear",
     [("returns.md", "Refunds"), ("cancellation.md", "Refunds for cancelled orders")]),
    ("opened headphones return ho sakta hai?", "mixed language",
     [("returns.md", "Headphones")]),
    ("laptop ki warranty kitne mahine ki hai?", "mixed language",
     [("warranty.md", "Laptops")]),
    ("Do you recycle old batteries?", "no answer", []),
    ("Do you offer gift wrapping?", "no answer", []),
]


async def main():
    pacer = _Pacer(settings.embedding_requests_per_minute)
    threshold = settings.policy_min_similarity
    passed = 0
    answer_scores, no_answer_scores = [], []

    async with async_session() as session:
        for question, kind, expected in CASES:
            await pacer.wait()
            vector = await embed_question(question)
            # min_similarity=-1 shows the top 3 whatever their score, to help tuning.
            top = await search_chunks(session, vector, limit=3, min_similarity=-1)
            kept = [t for t in top if t["similarity"] >= threshold]
            kept_keys = {(t["source_file"], t["section"]) for t in kept}

            if expected:
                ok = any(e in kept_keys for e in expected)
                match = [t["similarity"] for t in top if (t["source_file"], t["section"]) in expected]
                if match:
                    answer_scores.append(max(match))
            else:
                ok = not kept
                if top:
                    no_answer_scores.append(top[0]["similarity"])
            passed += ok

            print(f"\n[{'PASS' if ok else 'FAIL'}] ({kind}) {question}")
            expected_text = ", ".join(f"{f} > {s}" for f, s in expected) or "no_relevant_policy"
            print(f"  expected: {expected_text}")
            for t in top:
                mark = "kept" if t["similarity"] >= threshold else "dropped"
                print(f"  {t['similarity']:.3f}  {t['source_file']} > {t['section']}  ({mark})")

    await engine.dispose()

    print(f"\n{passed}/{len(CASES)} passed at policy_min_similarity = {threshold}")
    if answer_scores:
        print(f"Lowest score of a correct section:   {min(answer_scores):.3f}")
    if no_answer_scores:
        print(f"Highest top score, no-answer cases:  {max(no_answer_scores):.3f}")
    print("A good minimum similarity is between those two numbers (closer to the lower one).")


if __name__ == "__main__":
    kwargs = {}
    if sys.platform == "win32":
        kwargs["loop_factory"] = asyncio.SelectorEventLoop
    asyncio.run(main(), **kwargs)
