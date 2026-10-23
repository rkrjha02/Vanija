# Vanija

**Conversational Commerce Agent**

A WhatsApp-style AI sales agent that understands natural language, retrieves real product data through tools, manages a cart and orders safely, and answers policy questions with RAG. The current sample store sells electronics; the design is not limited to electronics.

**Status:** working locally with the full chat, cart, order and policy flow. Not yet deployed.

## Demo

<!-- Add demo GIF or live link here -->

## What it does

The customer chats naturally. The agent searches products, manages a cart, handles orders with a backend-enforced confirmation step, and answers store policy questions — all through a single chat interface.

**Browsing and adding to cart** (illustrative example):

> **Customer:** Show me phones under 15000
> **Agent:** Here are some phones under ₹15,000: *(product cards appear with Samsung Galaxy M15 at ₹8,999, Xiaomi Redmi Note 13 at ₹11,999, Realme Narzo 70 Pro at ₹14,999)*
> **Customer:** Add the second one
> **Agent:** Done! Xiaomi Redmi Note 13 (₹11,999) added to your cart. *(cart card appears)*
> **Customer:** Make it 3
> **Agent:** Updated! 3× Xiaomi Redmi Note 13 in your cart. Total: ₹35,997.

**Placing an order** (illustrative example):

> **Customer:** Place my order
> **Agent:** Here is your order summary. Please tap the Confirm button to place it. *(confirmation card with Confirm button appears)*
> *(Customer taps Confirm)*
> **System:** Order placed. Cash on Delivery.

The Confirm button goes directly to the backend — the LLM is never involved in the final order creation.

**Policy questions** (answers come from the sample policy files in `policies/`):

> **Customer:** Can I return opened headphones?
> **Agent:** Opened headphones and earphones cannot be returned for hygiene reasons unless they are defective. Defective opened headphones are replaced, not refunded.

## Architecture

```mermaid
graph TD
    subgraph Frontend
        UI[React + TypeScript]
    end

    subgraph Backend
        API[API layer — FastAPI]
        Agent[Agent loop]
        Provider[Provider layer — OpenAI-compatible]
        Tools[Tools — 9 functions]
        Embed[Embedding layer]
        Ingest[Ingest command]
        Data[Data layer — SQLAlchemy]
    end

    subgraph External services
        Groq[Groq — chat LLM]
        Gemini[Gemini — embeddings]
        Neon[Neon PostgreSQL + pgvector]
    end

    UI -->|HTTP| API
    API --> Agent
    API --> Data
    Agent --> Provider
    Agent --> Tools
    Agent --> Data
    Provider --> Groq
    Tools --> Data
    Tools --> Embed
    Ingest --> Embed
    Ingest --> Data
    Embed --> Gemini
    Data --> Neon
```

**How the layers work:**

- **API** — five FastAPI endpoints: create customer, send message, get history, confirm order, confirm cancel. The two button endpoints do not call the LLM.
- **Agent loop** — sends the LLM a system prompt, tool descriptions, a state block of recently shown products, and recent messages. The LLM replies with text or a tool request. The loop validates, executes, and repeats for up to 5 rounds. The agent reads and writes conversation data through the data layer.
- **Provider layer** — one OpenAI-compatible adapter, tested with Groq. Designed to work with other OpenAI-compatible providers.
- **Tools** — 9 functions: search_products, get_product_details, add_to_cart, update_cart_item, view_cart, view_saved_addresses, place_order, cancel_order, search_policies. Tools never write database queries — they call the data layer.
- **Embedding layer** — calls Google Gemini (`gemini-embedding-2`) for 768-dimensional vectors. Used by the ingest command and the search_policies tool.
- **Ingest command** — reads Markdown policy files, splits them into chunks by section, embeds each chunk, and stores them in PostgreSQL with pgvector.
- **Data layer** — all database access. Returns plain dictionaries, never ORM objects.

**Call direction (nothing calls upward):** `api` → `agent` and `data`; `agent` → `providers`, `tools`, and `data`; `tools` → `data` and `embeddings`; `ingest` → `data` and `embeddings`.

## Project structure

```
vanija/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI endpoints
│   │   ├── agent/          # Agent loop, prompt, validation, state block, confirm logic
│   │   ├── providers/      # OpenAI-compatible LLM adapter
│   │   ├── tools/          # 9 tool functions and their definitions
│   │   ├── embeddings/     # Gemini embedding client
│   │   ├── ingest/         # Policy ingest command
│   │   ├── data/           # SQLAlchemy models and all database access
│   │   ├── main.py         # FastAPI app entry point
│   │   └── config.py       # Settings from .env (pydantic-settings)
│   ├── migrations/         # Alembic migration files
│   ├── tests/              # pytest code tests and LLM behavior test set
│   ├── seed_data.py        # Sample product loader
│   ├── .env.example        # Setting names without real values
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.tsx          # Chat screen
│       ├── api.ts           # Backend API calls
│       └── components/      # Product, cart, order and cancel cards
├── policies/               # Markdown policy files (returns, warranty, shipping, etc.)
├── docs/                   # Design documents
├── CLAUDE.md               # Project instructions for Claude Code
└── .gitignore
```

## Key design decisions

1. **Tool calling with an agent loop.** The LLM chooses which tool to call and the backend validates and executes it. Multi-step requests work because a later tool can use a result from an earlier one. A hard limit of 5 rounds prevents runaway loops.

2. **The LLM proposes, the backend decides.** The LLM never accesses the database or creates orders. It proposes actions; the backend validates arguments, attaches the real customer ID, and executes. Prices, stock, cart totals, and order amounts come only from the database and backend code.

3. **Backend-enforced order confirmation.** `place_order` creates a pending record and shows a Confirm button. The button calls the backend directly — the LLM is not involved. The first tap wins at the database level: an atomic UPDATE changes the pending record from `waiting` to `used` only if it is still `waiting`. Stock is reduced in sorted product-ID order in one transaction to avoid deadlocks.

4. **Provider independence.** One OpenAI-compatible adapter, tested with Groq. Designed to work with other OpenAI-compatible providers. Switching provider or model is a `.env` change.

5. **RAG with database authority.** Policy questions use vector search (pgvector + Gemini embeddings) to find relevant policy chunks. The LLM answers only from the returned text. If a policy chunk and the database disagree (for example, on a price), the database wins.

6. **State block for resolving references.** The backend keeps up to 3 recent product lists (capped at 10 products total). "The second one" means item 2 of the latest list. "The second phone" means item 2 of the list labelled phones. The LLM never writes the state block — the backend updates it after each search.

## Tech stack

| Part | Choice |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Database | PostgreSQL on Neon (managed), pgvector extension |
| ORM / migrations | SQLAlchemy (async, psycopg 3), Alembic |
| Chat LLM | Groq (free tier), OpenAI-compatible adapter |
| Embeddings | Google Gemini (`gemini-embedding-2`, 768 dimensions) |
| Frontend | React 19, TypeScript, Vite |
| Backend tests | pytest |
| Frontend tests | Vitest |
| Settings | pydantic-settings, `.env` file |

## Getting started

Developed and tested on Python 3.14.7 and Node v24.4.1; other versions are untested.

### Prerequisites

- Python 3.14.7 and Node v24.4.1 (the versions it was tested on)
- Git
- A [Neon](https://neon.tech) PostgreSQL project
- A [Groq](https://console.groq.com) API key
- A [Google AI Studio](https://aistudio.google.com) API key (for embeddings — do **not** enable Cloud Billing on the project)

### Setup

```powershell
# Clone the repo
git clone <repo-url> vanija
cd vanija

# Create and activate the Python virtual environment
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run once:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

```powershell
# Install Python dependencies
pip install -r requirements.txt
```

### Configure .env

Copy `backend/.env.example` to `backend/.env` and fill in the values:

| Setting | Notes |
|---|---|
| `DATABASE_URL` | Neon **direct** connection string. The host must **not** contain `-pooler`. Change the start from `postgresql://` to `postgresql+psycopg://`. Must include `sslmode=require`. Example: `postgresql+psycopg://user:pass@ep-xyz-123456.us-east-2.aws.neon.tech/dbname?sslmode=require` |
| `TEST_DATABASE_URL` | A **separate** Neon project or branch — not the same as `DATABASE_URL`. The code tests drop and recreate all tables, so using the same database will destroy your data. Same format rules as above. |
| `GROQ_API_KEY` | From the Groq console. |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` |
| `GROQ_MODEL` | A Groq model that supports tool calling. Check the model's rate limits in the Groq console before choosing. |
| `GEMINI_API_KEY` | From Google AI Studio. |
| `EMBEDDING_PROVIDER` | `gemini` |
| `EMBEDDING_MODEL` | `gemini-embedding-2` |
| `EMBEDDING_DIMENSIONS` | `768` |

> **Warning:** If `DATABASE_URL` uses a pooled Neon address (host contains `-pooler`) or does not start with `postgresql+psycopg://`, the app will fail with a driver error at runtime. There is no startup check for this.

### Run migrations, seed data, and ingest policies

```powershell
# From backend/ with the venv active:

# Run database migrations (this also enables the pgvector extension)
alembic upgrade head

# Load sample products
python -m seed_data

# Ingest policy documents into the database
python -m app.ingest
```

### Start the app

```powershell
# Terminal 1: start the backend (from backend/)
uvicorn app.main:app --reload

# Terminal 2: start the frontend (from frontend/)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in a browser.

## Testing

All backend test commands run from `backend/` with the virtual environment active. Frontend tests run from `frontend/`.

### Code tests — backend (pytest)

```powershell
pytest
```

Requires `TEST_DATABASE_URL` in `.env`. These tests use a separate test database and **never call the LLM or embedding API** — all external calls are mocked. 15 test files covering: data layer, tools (product, cart, order, policy), agent validation, state block, provider adapter, buttons/confirm logic, embedding layer, chunking, ingest, and policy retrieval.

### Code tests — frontend (Vitest)

```powershell
cd frontend
npm test
```

3 test files covering: rupee formatting and spec labels (`format.test.ts`), card rendering for products, cart, order confirmation, cancel and order result (`cards.test.tsx`), and rich text rendering with XSS prevention (`RichText.test.tsx`). No external service calls.

### Retrieval tests

```powershell
python tests/policy_retrieval_set.py
```

12 policy questions tested against the dev database. **Calls the Gemini embedding API** (one real call per question). No chat LLM calls. Used to tune the minimum similarity threshold. Run `python -m app.ingest` first to load the policy files.

### LLM behavior test set

```powershell
python -m tests.llm_test_set              # all 30 cases, 3 runs each
python -m tests.llm_test_set --runs 1     # quick single pass
python -m tests.llm_test_set --case 5     # one case only
```

**Calls both Groq (chat LLM) and Gemini (embeddings).** Uses the test database. Each case sets up a starting situation (products, cart, shown lists, history), sends a customer message through the real agent loop, and checks which tool was called, with what arguments. Covers: greetings, product search, cart operations, order flow, policy questions, mixed-language input, ambiguous references, off-topic and rule-breaking attempts.

**Results to be added.**

## Known limitations

- **No timeout on the customer lock.** There is no application-level timeout on the customer lock. A second message from the same customer waits until the first finishes.
- **Cards are not redrawn after a reload.** The get-history endpoint returns text only. Product and cart cards from before the reload are not shown.
- **No streaming.** The backend returns one complete response per message. The frontend shows a typing indicator while waiting.
- **Automatic reply checks not implemented.** The design specifies that every ₹ amount in the LLM's reply must appear in that turn's tool results, and every duration must appear in the policy text. These checks are not yet in the LLM test set.
- **No validation of DATABASE_URL format.** A pooled Neon address (host contains `-pooler`) or a missing `postgresql+psycopg://` scheme prefix causes a driver error at runtime, not a clear startup message.
- **Sample data only.** The product catalog and policy documents are made-up examples for development. Replace them before any real use.

## Roadmap

- WhatsApp Business integration
- Online payments
- Authentication
- Order status and shipping tracking
- Product management
- Deployment

## Notes

- The product catalog is sample data for development. Prices, brands, and specs are illustrative.
- The policies in `policies/` are made-up examples. Replace them with real store policies before production use.
- Groq and Google AI Studio free tiers have rate limits. Heavy testing or multiple concurrent users may hit these limits.
