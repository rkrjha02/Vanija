# Project instructions: AI Conversational Sales Agent for Electronics

The full design is in @docs/design.md. Read it at the start of every session. Everything in it is LOCKED for Phase 1.

## Who I am working with
- A beginner in AI engineering with basic Python and good SQL knowledge, who wants to LEARN while building.
- Windows laptop, PowerShell, project in `D:\electronics-sales-agent`.

## How to work with me
1. **Build one slice at a time.** The slices are in section 13 of the design file. Build only the slice I name. Do not start or prepare anything from a later slice.
2. **Plan first.** At the start of each slice, give me a short plan (files to create, in what order, what I will be able to run at the end). Wait for my approval before writing code.
3. **Explain before you code.** Before showing or writing code, explain in simple language what it does and why. After it, explain the important lines. Define every technical term the first time you use it.
4. **No analogies.** Use concrete examples from this project instead.
5. **Small steps.** One concept or one file group at a time. Do not add explanation unrelated to the task.
6. **Ask before changing a locked decision.** If something in the design looks wrong, conflicts with another part, or is impossible, STOP and explain the problem with options and trade-offs. Do not silently choose a different approach.
7. **Ask at most one main question at a time.**
8. **Commit after each working step** with a short message. Do not commit until the step runs.

## Rules for the code
- Follow the folder structure and the call direction in section 3 of the design file: `api` -> `agent` -> `providers` and `tools` -> `data`. Nothing calls upward.
- Only `data/` talks to the database. Only `providers/` talks to an LLM provider. Tools never write queries.
- Data layer functions return plain data, never SQLAlchemy model objects.
- Race-sensitive changes (stock, status changes, marking a pending record used) are ONE conditional update statement plus a check of rows changed. Never load, change in Python, and save.
- The LLM never supplies a customer ID. The backend attaches it.
- Prices, totals, and stock come from the database and code only.
- Settings that may change (round limit, expiry minutes, number of recent messages, product cap) go in `config.py`, not in the code.
- Write code tests inside each slice. Code tests use a separate test database and never call the LLM.

## Secrets
- NEVER open, print, copy, or commit `.env`. Use `.env.example` to see setting names.
- I fill in `.env` myself. Do not ask me to paste keys or connection strings into the chat.
- `.env` must be in `.gitignore` from the first commit.
- Neon: use the DIRECT connection string (host name without `-pooler`), with the scheme `postgresql+psycopg://`.

## Environment
- Use PowerShell commands. Show each command and say what it does before I run it.
- The Python virtual environment lives in `backend/`.
