# AGENTS.md — InboxIQ Conventions

## Project
InboxIQ is an AI-powered unified email management web app. SPEC.md is
the product spec, ARCHITECTURE.md is the technical plan, README.md is
the developer onboarding doc. Always read all three before starting work.

## Stack (locked — do not deviate)
- Frontend: Next.js 14 (App Router) + TypeScript (strict) + Tailwind + shadcn/ui
- Backend: FastAPI (Python 3.11+) + Pydantic v2 + httpx async
- DB: Supabase (PostgreSQL) — RLS enabled on every table
- AI: OpenAI GPT-4o, JSON mode, official Python SDK
- Email: Gmail API via google-api-python-client
- Deploy: Vercel (frontend), Railway (backend)

## Folder structure
inboxiq/
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React components, kebab-case files
│   ├── lib/                 # Client utilities, API client, supabase clients
│   ├── types/               # Shared TS types
│   └── tests/               # Vitest + Playwright
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/         # One file per resource
│   │   ├── services/        # Business logic (gmail, openai, triage)
│   │   ├── models/          # Pydantic request/response models
│   │   ├── db/              # Supabase client + typed query helpers
│   │   ├── prompts/         # Static AI prompt constants
│   │   ├── core/            # Config, security, FastAPI dependencies
│   │   └── tasks/           # Background jobs (sync, AI worker)
│   ├── tests/
│   └── supabase/migrations/ # Numbered SQL files
├── plans/                   # Saved PLAN outputs from Codex chat
├── SPEC.md
├── ARCHITECTURE.md
├── README.md
└── AGENTS.md

## Coding rules
- TypeScript: strict mode, no `any` without a comment justifying.
- Python: full type hints, Pydantic models for every request/response,
  `from __future__ import annotations` at the top of every file.
- No raw SQL in routers. All DB access through `app/db/` helpers that
  return typed Pydantic models.
- No secrets in code. Config via env vars through `app/core/config.py`
  (Pydantic Settings).
- Async everywhere on backend: `httpx.AsyncClient`, `asyncio.gather`.
- Commit format: Conventional Commits (`feat(inbox): ...`, `fix(auth): ...`).
  Reference issue number: `feat(inbox): triage badges (#3)`.
- Branch names: `issue-N-short-slug`.

## Testing rules
- Backend: pytest + pytest-asyncio. Mock external APIs (Gmail, OpenAI)
  with `respx` for httpx + a stub Supabase client. Coverage ≥80% on
  `services/` and `routers/`.
- Frontend: Vitest for component logic. Playwright for ONE happy-path
  E2E per issue.
- Test files mirror source: `app/services/triage.py` →
  `tests/services/test_triage.py`.

## AI rules (critical)
- All OpenAI calls use JSON mode: `response_format={"type":"json_object"}`.
- Validate every AI response with a Pydantic model before use. If
  validation fails: log the raw response, mark email `ai_processed=false`
  to retry next cycle, do not raise.
- Triage system prompts are STATIC constants in `app/prompts/`. Never
  template user data into the system prompt — user data goes in the
  user message only.
- Each context mode has its own constant: `TRIAGE_PROMPT_JOB_HUNTING`,
  `TRIAGE_PROMPT_SHOPPING`, `TRIAGE_PROMPT_SCHOOL`, `TRIAGE_PROMPT_DAILY`.

## Security rules
- Supabase RLS on every table. App-layer checks are defense-in-depth,
  not the primary boundary.
- OAuth tokens never leave the backend. Frontend gets at most a boolean
  `connected` and the `email_address` string.
- Backend verifies the Supabase JWT on every authenticated request via
  a FastAPI dependency. Never trust a `user_id` from the request body.
- CORS allowlist is exact: deployed frontend URL + http://localhost:3000.
  No wildcards.
- Service role key is loaded ONLY in `app/db/supabase.py`. If you find
  it referenced anywhere else, that's a bug.

## When you're stuck or ambiguous
Stop and ask. List the decision points with options + tradeoffs. Do
not silently invent behavior the spec doesn't call for.
