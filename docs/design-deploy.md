# Deployment: Cloudflare Pages + Render + Neon

This file records the deployment decisions for the live app. It is referenced by `CLAUDE.md` and read at the start of each session.

---

## 1. Overview

| Part | Host | Type |
|---|---|---|
| Frontend | Cloudflare Pages | Static site (built with `npm run build`, output `dist/`) |
| Backend | Render free web service | Python, started with uvicorn |
| Database | Neon | Same project and `DATABASE_URL` as development |

---

## 2. Frontend (Cloudflare Pages)

- **Build command:** `npm run build`
- **Output directory:** `dist/`
- **Root directory (Cloudflare setting):** `frontend/`
- **Environment variable (set in Cloudflare Pages settings, not committed):** `VITE_API_BASE_URL` = the Render backend URL (e.g. `https://vanija-backend.onrender.com`). This is a build-time variable — Vite bakes it into the static JS at build time.
- When `VITE_API_BASE_URL` is not set (local development), the frontend falls back to `/api`, which the Vite dev proxy handles. No code change needed for local dev.
- The production frontend sends requests directly to the backend (no proxy). The Vite proxy only exists in `vite dev`.

---

## 3. Backend (Render free web service)

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Root directory (Render setting):** `backend/`
- **Python version:** Pin `PYTHON_VERSION=3.14.7` in Render's environment variables. This is the fully qualified version the tests were developed and run on. This means `requirements.txt` must install successfully on Python 3.14 on Linux; the first Render build will confirm. If a package fails to build a wheel for 3.14 on Linux, we decide then (options: pin an older Python, or find a compatible package version).
- Render sets the `PORT` environment variable automatically. The start command passes it to uvicorn with `--port $PORT`. No code change needed.
- No `--reload` in production.
- `run.py` is for local development only. Render uses the start command directly.

### Environment variables on Render

| Variable | Notes |
|---|---|
| `DATABASE_URL` | Same Neon direct connection string as development. See section 4. |
| `GROQ_API_KEY` | From the Groq console |
| `GROQ_MODEL` | The model name used in development |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` |
| `GEMINI_API_KEY` | From Google AI Studio |
| `EMBEDDING_PROVIDER` | `gemini` |
| `EMBEDDING_MODEL` | `gemini-embedding-2` |
| `EMBEDDING_DIMENSIONS` | `768` |
| `ALLOWED_ORIGINS` | The Cloudflare Pages domain (e.g. `https://vanija.pages.dev`) |
| `PYTHON_VERSION` | `3.14.7` |

`TEST_DATABASE_URL` is **not** set on Render — it is only needed for running tests locally.

---

## 4. Database (Neon — shared with development)

Live uses the **same Neon project and `DATABASE_URL`** as development. There is no separate live project.

- Use the DIRECT connection string (`postgresql+psycopg://`, host without `-pooler`, `sslmode=require`).
- Migrations (`alembic upgrade head`), seed data (`python -m seed_data`), and policy ingest (`python -m app.ingest`) are already applied to this database. No setup needed on Render for these.
- `pool_pre_ping=True` in the SQLAlchemy engine handles reconnection after Neon idle suspend.

### Consequences of sharing the database

- **Shared data:** Development and live see the same products, customers, orders, conversations, and policies. Changes made during development are visible to live users and vice versa.
- **Shared stock:** A local dev test that reduces stock affects the live app.
- **Schema changes reach live immediately:** Running `alembic upgrade head` locally updates the schema that the live backend is using.
- **Shared Neon quota:** Both environments share the Neon free-tier compute hours and storage.
- **`TEST_DATABASE_URL` stays separate:** Code tests (pytest) use a different Neon project. The LLM test set also uses `TEST_DATABASE_URL`. Only the policy retrieval test set (`tests/policy_retrieval_set.py`) reads from the shared database, and it is read-only.

---

## 5. Neon idle behavior

Free-tier Neon suspends compute after 5 minutes of inactivity. The Render free tier also spins down after 15 minutes of inactivity. The first request after both are idle is slow:

1. Render receives the request and cold-starts the Python process.
2. The first database query wakes Neon (can take a few seconds).
3. `pool_pre_ping=True` ensures stale pooled connections are replaced transparently.

This is expected on free tiers. The advisory lock connection (`locking.py`) also goes through the engine pool and benefits from `pool_pre_ping`.

---

## 6. New environment variables added for deployment

| Variable | Where | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | Cloudflare Pages (build-time) | Backend URL for the production frontend. Falls back to `/api` when not set. |
| `ALLOWED_ORIGINS` | Render (runtime) | Comma-separated production origins for CORS. Local dev origins are always included. |

---

## 7. Open items

- **Node version on Cloudflare Pages:** Not yet checked. Cloudflare Pages may default to an older Node version; the frontend was developed on Node v24.4.1.
- **Render `PORT` behavior:** To be confirmed on Render's docs — whether `$PORT` is always set and what its default value is.
- **Logging setup:** `logging.basicConfig` is currently called only in `run.py`, which is not used in production (`uvicorn app.main:app` does not import `run.py`). All `logger.warning()` and `logger.error()` calls in the app go to no handler under the production start command. Fix needed: add `logging.basicConfig(level=logging.INFO)` in `main.py`. Not yet implemented — waiting for approval.
- **No stock reset method exists:** `seed_data.py` skips when products already exist. There is no way to reset stock to starting values without manual SQL. If dev testing reduces stock, it affects the live app (shared database).
- **LLM test suite and the shared database:** The LLM test set (`tests/llm_test_set.py`) uses `TEST_DATABASE_URL` (separate), so it does not write to the shared database. The policy retrieval test set (`tests/policy_retrieval_set.py`) reads from `DATABASE_URL` (shared) but does not write to it.
- **Rate limits:** Not decided. No rate limiting is configured on the backend.
- **Wake-up endpoint:** Not decided. No mechanism to pre-warm Render or Neon after idle.
- **`lock_wait_seconds`:** Not decided. Current default is 90 seconds (`config.py`).
