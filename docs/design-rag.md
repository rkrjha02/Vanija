# Design addendum: Phase 2, Part 1: Policy questions (RAG)

This file adds policy question answering (RAG) to the Phase 1 system. Everything here is LOCKED unless it is listed under "Small details to settle while building". Where this file conflicts with `docs/design.md`, THIS FILE WINS for the items listed in section 2. If something here seems wrong or conflicts with another part, STOP and ask the user before changing it.

Same working rules as `CLAUDE.md`: one step at a time, plan first, explain before code, never open or print `.env`.

---

## 1. Goal

Today, when a customer asks "Can you explain the warranty?", the assistant says it has no information (rule 6 of the system prompt). With RAG (retrieval-augmented generation), the backend finds the relevant passages in the store's own policy documents and gives them to the LLM, and the LLM answers from those passages only.

Example: "Can I return headphones if I've opened the box?" -> the backend finds the matching policy section and the LLM answers from it.

RAG is just another tool. The architecture does not change.

---

## 2. What this changes in `docs/design.md`

| Part of design.md | Change |
|---|---|
| Section 6, Tools | There are now **9 tools**. Add tool 9, `search_policies` (section 7 below). |
| Section 9, system prompt rule 6 | Replace "tell the customer you don't have that information yet" with the new rule in section 8 below. |
| Section 3, folder structure | Add `backend/app/embeddings/` (embedding layer), `backend/app/ingest/` (the ingest command), and `policies/` at the repo root (Markdown policy files). Call direction: `tools` -> `embeddings` and `data`; `ingest` -> `embeddings` and `data`. |
| Section 7, Database | Add 2 tables (section 3 below), so there are now 12 tables. Enable the `pgvector` extension through an Alembic migration. |
| Section 12, Testing | Add the policy tests in section 10 below. Extend the reply check (section 9). |
| Section 4, Rule 3 (failures) | A failed embedding call inside the tool is handled like a database error: the tool returns a generic "system error" status, with no technical text to the LLM or customer. |

Unchanged: all 8 earlier tools, the order flow, the state block, the API contract, and the rule that prices, stock and specs come only from the database tools. If a policy chunk and the database ever disagree, the database wins.

---

## 3. Database: pgvector in Neon, two new tables

**pgvector** is a PostgreSQL extension that adds a `vector` column type and similarity search. Neon supports it. It does not create tables; we design them. Enable it once in an Alembic migration.

### policy_documents (one row per policy file)
| Column | Notes |
|---|---|
| `id` | Primary key |
| `title` | Document title |
| `source_file` | The Markdown file name (unique) |
| `content_hash` | A short fingerprint of the file's text. If unchanged on re-run, the ingest command skips the file (saves the free embedding quota). |
| `updated_at` | |

### policy_chunks (one row per chunk)
| Column | Notes |
|---|---|
| `id` | Primary key |
| `document_id` | Foreign key to `policy_documents`, deleted together with its document |
| `chunk_index` | Order of the chunk inside the document |
| `section` | The section heading (needed for the tool output) |
| `chunk_text` | The chunk text, WITH the document title and heading added at the start (see section 5) |
| `embedding` | `vector(768)` |

The size 768 matches the embedding model's output setting. Changing the embedding model later means re-embedding every chunk and a migration to change the column size.

Replacing a document = delete all chunks with that `document_id`, then insert the new ones, in one transaction.

---

## 4. Embedding layer (separate from the chat provider layer)

- Lives in `backend/app/embeddings/`. Only this folder talks to the embedding API. The chat provider layer is not used for embeddings.
- Model: Google Gemini embeddings, `gemini-embedding-001`, output size **768** dimensions. Free tier, no billing.
- Settings in `.env` (names to be proposed by Claude Code): embedding provider, model name, dimensions (768), API key. The Gemini API key is a NEW key the user creates in Google AI Studio and puts in `.env` themselves.
- **NEVER enable Cloud Billing on the Google project that owns the key.** Staying without billing keeps the free tier.
- Free-tier limits for `gemini-embedding-001` as reported (not guaranteed, may change): 100 requests per minute, 30,000 tokens per minute, 1,000 requests per day. The ingest command must pace its calls to stay under them (one policy collection of about 40 chunks of about 200 tokens is about 8,000 tokens, so it fits within a minute; larger collections must be spread out).
- Free-tier content may be used by Google to improve its products; paid-tier content is not. Fine for learning with fake questions and public policy text. Real clients should use the paid tier, after reading its terms.
- The same model must be used for the chunks and for the customer's question. Vectors from different models cannot be compared.
- Before implementing, CHECK Google's current docs for: (a) whether 768-dimension vectors must be normalized before cosine similarity, (b) whether the API has a setting that marks a text as a document or as a question, (c) whether a newer embedding model (for example "Gemini Embedding 2") is recommended. If a newer model is recommended, tell the user BEFORE fixing the column size.

---

## 5. Chunking (LOCKED)

- Split each Markdown file by `##` sections. Each section = one chunk.
- Put the document title and the heading at the start of the chunk text, for example: `Warranty Policy > Phones: Phones have a 12-month warranty. Water damage is not covered.`
- If a section is too long, split it by paragraph and keep the same title and heading prefix on every piece.
- The model accepts up to 2,048 tokens per input; our chunks are far below that.
- Semantic chunking is NOT used now. It may be added later only for documents without headings or sections that are still too long, and only if the policy retrieval tests show misses.

---

## 6. Ingest command and policy files (LOCKED)

- Policies are Markdown files in `policies/` at the repo root.
- One command (in `backend/app/ingest/`) reads each file and, for each CHANGED file (compare `content_hash`): splits it into chunks, creates the embeddings, then in one short database transaction deletes that document's old chunks and inserts the new ones. Create all embeddings BEFORE opening the transaction, so the transaction stays short. If anything fails, the old chunks stay and the assistant is never left with half a policy.
- Unchanged files are skipped.
- Later, an upload screen would call the same code. Uploading and PDF/Word ingestion are deferred.

Rules for writing the policy files:
- Each topic gets its own `##` section.
- If rules differ by product category (for example phones vs headphones), use separate sections.
- Policies must NOT contain prices, stock, or product specs. Those change often and come from the database tools.
- Sample files (returns, warranty, shipping, cancellation, COD) are clearly marked as made-up examples for the user to edit.

---

## 7. Tool 9: search_policies (reads)

| Input | Required | Details |
|---|---|---|
| `question` | Yes | A short, self-contained question written by the LLM. Non-empty, with a maximum length (value to be set). |

The tool description must tell the LLM to include the subject in the question. After a talk about headphones, "what about the warranty on that?" must become "What is the warranty period for headphones?" Otherwise the embedding matches nothing useful.

How it works: the backend embeds the question with the same model, then asks pgvector for the closest chunks (cosine similarity), drops chunks below the minimum similarity, and returns up to 3.

Output:
- `status`: `found` or `no_relevant_policy`
- `results`: up to 3 items, each with `document_title`, `section`, `text`

Rules:
- No card is created, and the state block is NOT changed.
- The customer ID is not used (policies are the same for every customer).
- If no chunk reaches the minimum similarity, return `no_relevant_policy`.

Config settings (not hard-coded):
- Chunks returned: 3 (more chunks means more tokens read on every such request, and token use matters on the Groq free tier).
- Minimum similarity: start on the lenient side and tune it from the retrieval tests. Too high gives "I don't know" for valid questions phrased differently (for example mixed Hindi and English). Too low behaves like "always return the closest 3" and can make the LLM stretch unrelated text into an invented policy.

---

## 8. System prompt change (replaces rule 6)

New rule 6, written as one short line (final wording tuned with the tests):
"For policy questions (returns, warranty, shipping, cancellation, payment), call the policy search tool and answer ONLY from its text. If it finds nothing relevant, or the text does not answer the question, say you don't have that information. Never state a policy from memory."

With 9 tools, the tool descriptions must make the difference between product tools and the policy tool clear. The test set checks that the model picks the right one.

---

## 9. Reply check (extends the automatic rules)

Phase 1 rule: every ₹ amount in the reply must appear in that turn's tool results.
Added: any duration in the reply (for example "7 days", "12 months") must appear in that turn's policy text. This protects against a wrong "7 days" when the policy says 10.

---

## 10. Tests

### Retrieval tests (no chat LLM; cheap)
A list of policy questions, each with the section that should come back. Used to tune the minimum similarity and to compare chunking strategies later. Include: a question with a clear answer, a phrasing that differs from the policy wording, a mixed-language question (for example "opened headphones return ho sakta hai?"), and a question with NO answer in the policies (must return `no_relevant_policy`).

### Code tests for ingest
- A changed file is re-embedded; an unchanged file is skipped.
- Replacing a document deletes the old chunks and inserts the new ones.
- A failure halfway leaves the old chunks in place (rollback).
- Embedding calls are mocked in code tests (no real API calls).

### LLM behavior tests (added to the fixed test set; run 3 times each)
| Customer says | Expected |
|---|---|
| "Can I return opened headphones?" | `search_policies`, then an answer from the text |
| "Is water damage covered for phones?" | `search_policies` with phones in the question |
| "opened headphones return ho sakta hai?" | `search_policies`, correct chunk found |
| "Do you recycle old batteries?" | `search_policies`, then "I don't have that information" |
| "Show phones under 15000" | `search_products`, NOT the policy tool |
| After talking about headphones: "what about the warranty on that?" | `search_policies` with headphones in the question |
| "What does Phone A cost and what's its warranty?" | Both a product tool and the policy tool |

---

## 11. Build order (RAG steps)

| Step | What | Result |
|---|---|---|
| R0 | USER creates the Gemini API key in AI Studio (no Cloud Billing) and puts it in `.env`. Create sample policy files in `policies/`. | Key and sample files ready |
| R1 | Enable pgvector, create the two tables through Alembic, build the embedding layer, smoke-test one embedding call | One text turns into a 768-number vector and can be stored |
| R2 | The ingest command with code tests | `policies/` loads into the database; re-running skips unchanged files |
| R3 | The retrieval function, the retrieval test list, and tuning of the minimum similarity | The right section comes back; unanswerable questions return `no_relevant_policy` |
| R4 | Tool 9, the prompt change, the LLM test cases, end-to-end through the chat | Ask a policy question through the chat and get a grounded answer |

---

## 12. Small details to settle while building
- Names of the embedding settings in `.env` and `config.py`
- The minimum similarity value, and the maximum length of `question`
- How Google counts batched texts against the free-tier limits
- The exact wording of the tool description and of the new rule 6

## 13. Deferred
Semantic chunking fallback, an upload screen for policies, PDF and Word ingestion (with OCR), keyword-plus-vector hybrid search, re-ranking, and a command to re-embed everything when the embedding model changes.
