# CLAUDE.md — InboxIQ conventions

## Project
InboxIQ is an AI-powered email triage app. README.md covers setup and usage;
docs/architecture.md covers the design. Read both before starting work.

## Stack
- Frontend: Next.js 14 (App Router) + TypeScript (strict) + Tailwind + shadcn/ui + TanStack Query
- Backend: FastAPI (Python 3.11) + Pydantic v2 + httpx
- DB/Auth: Supabase (Postgres) with RLS enabled on every table
- AI: OpenRouter with Anthropic fallback, via `app/services/ai_client.py`
- Email: Gmail API via google-api-python-client
- Deploy: Vercel (frontend), Railway (backend)

## Folder structure
```
InboxIQ/
├── frontend/
│   ├── app/            # Next.js App Router pages
│   ├── components/     # React components, kebab-case files
│   ├── lib/            # API client, React Query hooks, Supabase clients
│   ├── types/          # Shared TS types
│   └── tests/          # Vitest (unit) + Playwright (e2e)
├── backend/
│   ├── app/
│   │   ├── core/       # Config, auth, errors, background tasks, clock, logging
│   │   ├── routers/    # One file per resource; thin
│   │   ├── services/   # Business logic (Gmail, AI, triage, contacts, digest)
│   │   ├── db/         # Typed Supabase queries; no FastAPI imports
│   │   ├── models/     # Pydantic models
│   │   ├── prompts/    # Static AI prompt constants
│   │   ├── tasks/      # AI worker and scheduler
│   │   └── demo/       # DEMO_MODE fixtures and seeding
│   ├── tests/          # Mirrors app/
│   └── supabase/       # Numbered SQL migrations + RLS tests
└── docs/               # Architecture and screenshots
```

## Coding rules
- Layering: routers → services → db. db helpers never import FastAPI or services.
- Errors: raise `app.core.errors` domain exceptions (`NotFoundError`,
  `ConflictError`, `BadRequestError`, `RateLimitedError`). `HTTPException` is
  used only in `app/core/auth.py`. Responses use `{"detail": {"code", "message"}}`.
- Background work: `app.core.background.spawn`, never a bare `asyncio.create_task`.
- Time: `app.core.clock.utc_now()` / `utc_today()`; never naive datetimes.
- Python: full type hints, `from __future__ import annotations`, Pydantic models
  for every request and response. Config comes only from `app/core/config.py`.
- TypeScript: strict mode; no `any` without a comment explaining why. Server
  state goes through React Query hooks in `lib/queries/`.
- Commits: Conventional Commits (`feat(inbox): ...`, `fix(auth): ...`).

## Testing rules
- Run `make lint typecheck test` before committing.
- Backend: pytest. Mock Gmail and LLM providers; for query-builder behavior use
  the real client with respx (see `tests/db/test_query_builders.py`) rather than
  MagicMock chains, which accept calls the real builder rejects.
- Frontend: Vitest for components and hooks; Playwright for one happy path per
  page, with every API call mocked through `tests/e2e/fixtures.ts`.
- Bug fixes start with a failing test.

## AI rules
- Validate every model response with a Pydantic model before use. On failure,
  record the attempt and leave the email unprocessed so the worker retries
  (up to 3 attempts).
- System prompts are static constants in `app/prompts/`, one per context mode.
  Email content goes in the user message only.
- Never log full model responses; they contain email content.

## Security rules
- RLS on every table; app-level user scoping is defense in depth, not the boundary.
- OAuth tokens never leave the backend.
- Every authenticated route uses `get_current_user`; never trust a `user_id`
  from the request body.
- The service-role key is read only in `app/db/supabase.py`.
- OAuth `return_to` must be a same-origin path (`is_safe_return_path`).

## When stuck
Stop and ask. List the decision points with options and trade-offs; don't
invent behavior the README or architecture doc doesn't describe.
