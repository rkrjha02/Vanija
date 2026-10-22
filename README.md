# Electronics Sales Agent

AI conversational sales agent for an electronics store. A customer chats naturally, and the agent understands needs, searches real product data, manages a cart, and helps place Cash on Delivery orders.

Phase 1 is a local learning project with a web chat interface (React frontend, FastAPI backend, PostgreSQL on Neon).

## Architecture

```
api  ->  agent  ->  providers (Groq / OpenAI-compatible LLM)
                ->  tools     ->  data (PostgreSQL)
```

- The LLM proposes actions via tool calls; the backend validates, executes, and returns results.
- Prices, stock, and totals come only from the database and code, never from the LLM.
- Order confirmation and cancellation go through dedicated backend endpoints, not the LLM.

## Prerequisites

- Python 3.10+
- Node.js 18+
- A [Neon](https://neon.tech) PostgreSQL project (free tier works)
- A [Groq](https://console.groq.com) API key (free tier works)

## Setup

### 1. Clone and enter the repo

```powershell
git clone <repo-url>
cd electronics-sales-agent
```

### 2. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `backend/.env` from the example:

```powershell
copy .env.example .env
```

Fill in your values:

| Setting | Where to get it |
|---|---|
| `DATABASE_URL` | Neon dashboard → Connection Details → **Direct** connection string. Change `postgresql://` to `postgresql+psycopg://`. Must include `?sslmode=require`. |
| `TEST_DATABASE_URL` | A separate Neon project or branch for tests. Same format. |
| `GROQ_API_KEY` | Groq console → API Keys |
| `GROQ_MODEL` | A Groq model that supports tool calling (check Groq docs for current options) |

### 3. Run database migrations

```powershell
cd backend
alembic upgrade head
```

### 4. Seed products

The test database is seeded automatically by the test suite. For the development database, use the Alembic seed migration or insert products manually.

### 5. Frontend

```powershell
cd frontend
npm install
```

## Running

### Backend

```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Open `http://localhost:8000/docs` for the Swagger UI.

### Frontend

```powershell
cd frontend
npm run dev
```

The frontend runs at `http://localhost:5173`.

## Testing

### Code tests (pytest)

These use the test database and never call the LLM. Run from `backend/`:

```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest -v
```

### LLM behavior tests

These send real messages through the agent loop to Groq and check which tool the LLM calls. They use Groq quota, so run them only when changing the model, provider, or prompt.

```powershell
cd backend
.venv\Scripts\Activate.ps1
python -m tests.llm_test_set                # all 25 cases, 3 runs each
python -m tests.llm_test_set --runs 1       # quick single pass
python -m tests.llm_test_set --case 5       # one case only
```

## Project structure

```
electronics-sales-agent/
├── backend/
│   ├── app/
│   │   ├── main.py          FastAPI application
│   │   ├── config.py         Settings from .env
│   │   ├── api/              Endpoints (chat, customers, history, orders)
│   │   ├── agent/            Agent loop, system prompt, validation, state block
│   │   ├── providers/        OpenAI-compatible LLM adapter (Groq, Gemini, Ollama)
│   │   ├── tools/            8 tools (search, details, cart, orders)
│   │   └── data/             SQLAlchemy models and data-layer functions
│   ├── migrations/           Alembic migrations
│   ├── tests/                pytest tests and LLM behavior test set
│   ├── .env.example          Setting names (no real values)
│   └── requirements.txt
├── frontend/                 React + TypeScript chat interface
├── docs/design.md            Full design document (locked for Phase 1)
└── CLAUDE.md                 AI assistant instructions
```

## API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/customers` | POST | Create a new customer (returns a random ID) |
| `/chat` | POST | Send a message, get the agent's reply + cards |
| `/history/{customer_id}` | GET | Load recent messages (text only) |
| `/orders/confirm` | POST | Confirm a pending order (no LLM call) |
| `/orders/cancel` | POST | Confirm order cancellation (no LLM call) |

## Design decisions

See `docs/design.md` for the full locked design. Key points:

- One message at a time per customer (PostgreSQL advisory lock)
- Maximum 5 agent rounds per customer message
- Stock is checked but not reserved when adding to cart
- Orders use a pending confirmation flow with 15-minute expiry
- Duplicate order prevention at the database level
