---
title: InboxIQ Foundation — Issue 1A Design
date: 2026-05-04
status: approved
---

# InboxIQ Foundation — Issue 1A Design

## Context

This spec covers Issue 1A: full-stack scaffolding for InboxIQ. A previous PR (#11) landed
partial backend code (Gmail OAuth, JWT auth, flat app structure) and 5 Supabase migrations
with non-spec naming. **Approach A (delete and rebuild)** was chosen: all existing backend
app files and migrations are deleted, then the spec-prescribed structure is built from scratch.
The existing frontend tree is kept and extended.

---

## Approach

**Delete first, then build.** No parallel structures, no leftover imports.

Files deleted before any new code is written:
- `backend/app/auth_jwt.py`, `config.py`, `gmail_fetch.py`, `gmail_oauth.py`, `main.py`,
  `oauth_state.py`, `supabase_client.py`
- `backend/app/routers/emails.py`, `routers/gmail_auth.py`
- `backend/app/__pycache__/` and `routers/__pycache__/`
- `supabase/migrations/001_connected_accounts.sql` through `005_contact_tags.sql`

Kept: `backend/requirements.txt`, `backend/Procfile`, `backend/runtime.txt`, full `frontend/` tree.

---

## Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, CORS, lifespan, /health, routers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic Settings singleton (all env vars)
│   │   └── auth.py              # verify_jwt, UserClaims, get_current_user dep
│   ├── db/
│   │   ├── __init__.py
│   │   ├── supabase.py          # get_anon_client() + get_service_client()
│   │   └── users.py             # get_user(), update_default_context()
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py              # User Pydantic model
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py              # 501 stubs: GET /auth/gmail/start, /callback
│   │   └── users.py             # GET /users/me, PATCH /users/me/context
│   ├── services/                # empty __init__.py placeholder
│   ├── prompts/                 # empty __init__.py placeholder
│   └── tasks/                   # empty __init__.py placeholder
├── scripts/
│   └── print_migrations.py
├── supabase/
│   ├── migrations/
│   │   ├── 001_users.sql
│   │   ├── 002_connected_accounts.sql
│   │   ├── 003_emails.sql
│   │   ├── 004_contact_tags.sql
│   │   ├── 005_auth_trigger.sql
│   │   └── 006_color_palette.sql
│   └── tests/
│       └── test_rls.sql
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── core/
│   │   └── test_auth.py         # HS256 happy/expired/mangled; ES256 with mocked JWKS
│   └── routers/
│       └── test_users.py        # GET /users/me; PATCH /users/me/context
├── requirements.txt             # all packages pinned per spec + dev deps
├── .env.example
├── Procfile                     # kept
└── runtime.txt                  # kept
```

### Key backend components

**`app/core/config.py`** — Pydantic Settings with all env vars needed across all 7 issues:
- Required: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`,
  `SUPABASE_JWT_SECRET` (optional str, legacy HS256), `GMAIL_CLIENT_ID`,
  `GMAIL_CLIENT_SECRET`, `GMAIL_REDIRECT_URI`, `OAUTH_STATE_SECRET`, `OPENAI_API_KEY`,
  `FRONTEND_URL`
- Optional with defaults: `ENVIRONMENT` (dev), `LOG_LEVEL` (INFO), `ALLOWED_ORIGINS`
  (comma-separated, defaults to FRONTEND_URL + localhost:3000), `TOKEN_ENCRYPTION_KEY`
  (None), `SENTRY_DSN` (None), `GIT_SHA` (dev)
- Exports `settings` singleton

**`app/core/auth.py`** — `verify_jwt(token) -> UserClaims`. Reads `alg` header; HS256 uses
`SUPABASE_JWT_SECRET`; ES256/RS256 fetches JWKS from Supabase and caches in-memory 5 min.
`UserClaims` has `user_id: UUID`, `email: str`. `get_current_user` FastAPI dep raises 401
with `code: "auth_invalid"` or `code: "auth_expired"` — no stack trace leak.

**`app/db/supabase.py`** — Two functions: `get_anon_client()` (respects RLS) and
`get_service_client()` (bypasses RLS). Service role key referenced ONLY here and in
`core/config.py`.

**`app/main.py`** — CORS from `settings.allowed_origins` (no wildcards). Async `/health`
probes Supabase and OpenAI with 1s timeout via `asyncio.gather`; returns 200 with
`"ok"|"down"`, never 503. Lifespan logs boolean presence of every required env var.

**`app/routers/auth.py`** — Both endpoints return `HTTP 501 Not Implemented`. Issue 1B
replaces these.

### Migrations

Six idempotent SQL files, each with `CREATE TABLE IF NOT EXISTS`, indexes, and full RLS
policies. Content exactly as specified: 001 users, 002 connected_accounts, 003 emails,
004 contact_tags, 005 auth trigger function, 006 color palette function.

### Tests

`tests/core/test_auth.py`: HS256 happy path, expired token, mangled token, missing sub
claim; ES256 with respx-mocked JWKS endpoint.

`tests/routers/test_users.py`: GET /users/me happy/401-no-token/401-mangled;
PATCH /users/me/context happy/422-invalid-context.

`supabase/tests/test_rls.sql`: 8 adversarial queries that must return 0 rows when run as
user A against user B's data (emails, accounts, users row, contact_tags, oauth_token).

---

## Frontend Structure

Existing tree kept and extended. `app/login/` deleted and replaced by `app/auth/sign-in/`.

```
frontend/
├── app/
│   ├── layout.tsx               # updated: sidebar nav (5 routes) + sign-out button
│   ├── page.tsx                 # updated: "Home" placeholder
│   ├── inbox/page.tsx           # new stub
│   ├── packages/page.tsx        # new stub
│   ├── contacts/page.tsx        # new stub
│   ├── settings/page.tsx        # new stub
│   ├── auth/
│   │   ├── sign-in/page.tsx     # new: magic-link form (replaces login/)
│   │   └── callback/route.ts    # kept as-is
│   └── login/                   # DELETED
├── lib/
│   ├── supabase/                # kept (client.ts, server.ts, middleware.ts)
│   ├── api.ts                   # new: typed fetch wrapper, ApiError class
│   └── utils.ts                 # kept
├── types/
│   └── index.ts                 # new: shared TS types
├── middleware.ts                 # updated: protect 5 routes, redirect to /auth/sign-in
├── .env.example                 # new
└── package.json                 # updated: add @tanstack/react-query, date-fns, sonner + vitest/playwright
```

**`lib/api.ts`** — Typed fetch wrapper reading `NEXT_PUBLIC_API_URL`. Attaches
`Authorization: Bearer <token>` from current Supabase session. Throws
`ApiError(status, code, message)` on non-2xx.

**`middleware.ts`** — Protects `/`, `/inbox`, `/packages`, `/contacts`, `/settings`.
Unauthenticated users redirected to `/auth/sign-in`.

---

## Repo-level Files

**`Makefile`** — `install`, `dev`, `test`, `lint`, `typecheck`, `format`, `migrations`.
`make dev` uses `npx concurrently` for frontend (3000) + backend (8000). `make migrations`
runs `python backend/scripts/print_migrations.py`.

**`.github/workflows/ci.yml`** — PR trigger. Two parallel jobs: Node 20 (lint + typecheck)
and Python 3.11 (ruff + mypy + pytest).

**`README.md`** — "Migrations" subsection added with print script instructions.

**Unchanged:** `.gitignore`, `.editorconfig`, `CLAUDE.md`, `SPEC.md`, `ARCHITECTURE.md`.

---

## Constraints

- Service role key referenced ONLY in `app/core/config.py` and `app/db/supabase.py`.
- No wildcards in CORS.
- TypeScript strict throughout; all Python fully typed with `from __future__ import annotations`.
- No business logic beyond the above — foundation only.
