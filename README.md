# InboxIQ 📬

> AI-Powered Unified Email Management App

---

## Overview

InboxIQ aggregates all your email accounts into one intelligent
dashboard. Users set their current "life context" — job hunting,
online shopping, school applications — and the AI automatically
triages every incoming email by urgency, extracts deadlines and
action items, and tracks package pickup codes.

The problem: people who manage multiple inboxes miss critical
emails (interview invites, OA deadlines, pickup code expirations)
because they are buried under ads and promotions. InboxIQ solves
this by acting as an AI-powered filter that shows users only what
actually matters — in real time, across all their accounts.

---

## Revenue Model

InboxIQ operates on a freemium SaaS model:

| Tier     | Price          | Features                                                                    |
| -------- | -------------- | --------------------------------------------------------------------------- |
| **Free** | $0/month       | 1 connected inbox, basic AI triage, pickup tracker                          |
| **Pro**  | $8/month       | Unlimited inboxes, full context modes, contact tagging, deadline extraction |
| **Team** | $20/user/month | Shared inbox labels, admin dashboard, priority support                      |

**Additional revenue streams:**

- Annual plan discount (20% off Pro) to improve retention
- Enterprise licensing for organizations managing shared inboxes

**Market validation:** Gmail has 1.8B active users. Tools like
Superhuman ($30/month) demonstrate strong willingness to pay for
email productivity. InboxIQ targets a lower price point with
broader multi-account support as its primary differentiator.

---

## Core Features

- 🔗 **Multi-inbox aggregation** — Connect Gmail & Outlook via OAuth
- 🤖 **AI email triage** — Classify emails into 🔴 Action Required /
  🟡 Worth Reading / ⚪ Auto-Archive based on life context
- ⏰ **Deadline extraction** — AI pulls due dates from email body
  and surfaces them as reminders
- 📦 **Package tracker** — Auto-detect pickup codes, one-tap
  mark as used
- 🏷️ **Contact tagging** — Flag professors, friends, and recruiters
  for instant highlight
- 📊 **Daily digest dashboard** — Morning briefing of everything
  that needs attention today

---

## Tech Stack

| Layer      | Technology                                  |
| ---------- | ------------------------------------------- |
| Frontend   | Next.js 14 + Tailwind CSS + shadcn/ui       |
| Backend    | FastAPI (Python)                            |
| AI         | OpenAI GPT-4o                               |
| Email APIs | Gmail API + Microsoft Graph API (OAuth 2.0) |
| Database   | PostgreSQL via Supabase                     |
| Auth       | Supabase Auth                               |
| Deployment | Vercel (frontend) + Railway (backend)       |

---

## Team

| Role              | Name         | Responsibilities                                                    |
| ----------------- | ------------ | ------------------------------------------------------------------- |
| Proposer (Client) | Ting Li      | Spec, issue creation, PR review, acceptance testing, Demo Day pitch |
| Developer         | John Huang   | Architecture, implementation, testing, PR submission                |
| Development Fee   | 50 GIX Bucks | Paid on final delivery                                              |

---

## Repository Structure

```
inboxiq/
├── frontend/          # Next.js app
├── backend/           # FastAPI app
├── SPEC.md            # Full project specification
├── ARCHITECTURE.md    # Developer's architecture document (by John Huang)
├── CLAUDE.md          # AI-assisted development config
├── .cursorrules       # Cursor rules for agentic engineering
└── README.md          # This file
```

---

## Branch Protection Rules

- `main` branch requires **at least 1 approving review** before merge
- All features must be submitted via Pull Request referencing a GitHub Issue
- Direct pushes to `main` are disabled
- Developer must respond to all review comments within **48 hours**
- Proposer must review all PRs within **48 hours**

---

## Development Timeline (2 Weeks)

> **Mid-point check completed: May 4, 2026.**
> Developer is **behind schedule**. Check-ins 2 and 3 are not met. See bug issues #12–#17 for detailed findings.

| Milestone             | Deadline             | Status | Required Progress                                                                                                                             | Acceptance Gate                                                | Notes |
| --------------------- | -------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ----- |
| ✅ **Check-in 1**     | End of Week 1, Day 3 | **Partial** | OAuth login working for Gmail; emails fetched and stored in DB; project deployed to staging URL; ARCHITECTURE.md submitted | Proposer reviews Architecture PR within 48 hours | ARCHITECTURE.md merged (PR #2). Gmail OAuth merged late (PR #11, May 2). Emails are **not stored in DB** — fetched live only. No staging deployment confirmed. |
| ❌ **Check-in 2**     | End of Week 1, Day 6 | **Not met** | AI triage pipeline working (3-category classification + summary); context mode switcher functional; unified inbox page live on staging | Proposer conducts acceptance test on inbox triage accuracy | No AI triage exists. No context switcher. No `/inbox` page. OpenAI not integrated. See bugs [#12](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/12), [#13](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/13), [#14](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/14). |
| ❌ **Check-in 3**     | End of Week 2, Day 3 | **Not met** | Package tracker complete with auto-detection and mark-as-used; deadline extraction working; contact tagging functional; all MVP issues closed | Proposer files bug reports; developer resolves within 48 hours | Package tracker missing (bug [#15](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/15)). Dashboard missing (bug [#16](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/16)). DB schema incomplete (bug [#17](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/17)). Issues #4–#10 all still open. |
| 🏁 **Final Delivery** | End of Week 2        | **At risk** | All MVP features polished and deployed to production URL; README updated; tests passing; demo-ready                                           | Final acceptance test by proposer; GIX Bucks paid on approval  | 6 blocker bugs filed (issues #12–#17). Developer must resolve all blockers and complete open issues #4–#10 to qualify for final payment. |

### Mid-Point Assessment (May 4, 2026)

**What is working:**
- Supabase magic-link authentication (`/login`)
- Gmail OAuth 2.0 flow (connect account, token stored in `connected_accounts`)
- Basic email metadata fetch (subject, sender, snippet — up to 15 messages)

**What is missing (all blockers):**

| Bug | Issue | Severity |
| --- | ----- | -------- |
| [#12](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/12) AI triage badges and summaries absent | #5 | Blocker |
| [#13](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/13) Context mode switcher absent | #5 | Blocker |
| [#14](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/14) Email body not fetched; no OpenAI client | #5 #6 #8 | Blocker |
| [#15](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/15) Package tracker page missing | #8 | Blocker |
| [#16](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/16) Dashboard home page missing | #9 | Blocker |
| [#17](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/17) `emails` and `contact_tags` DB tables not created | #4–#8 | Blocker |

All 6 bugs must be resolved within 48 hours per contract terms.

---

## GitHub Issues

The full project is decomposed into the following issues.
Each PR must reference its corresponding issue.

| #   | Issue                                               | Epic        |
| --- | --------------------------------------------------- | ----------- |
| 1   | Project Setup & Repo Scaffolding                    | `setup`     |
| 2   | Database Schema & Supabase Auth                     | `setup`     |
| 3   | Gmail OAuth & Email Sync Pipeline                   | `auth`      |
| 4   | AI Triage Pipeline (classify + summarize + extract) | `ai`        |
| 5   | Unified Inbox Page                                  | `inbox`     |
| 6   | Dashboard & Daily Digest                            | `dashboard` |
| 7   | Package Tracker Page                                | `tracker`   |
| 8   | Contact Tags & Settings Pages                       | `contacts`  |

---

## Acceptance Criteria Summary

Each issue has its own detailed acceptance criteria.
High-level gates for final delivery:

- [x] User can connect at least 1 Gmail account via OAuth ✅ working
- [ ] All emails displayed in unified inbox with triage badges ❌ bug [#12](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/12)
- [ ] Switching context mode visibly changes triage results ❌ bug [#13](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/13)
- [ ] AI summary visible on every email card ❌ bug [#12](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/12), [#14](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/14)
- [ ] At least 1 deadline correctly extracted from a real email ❌ not implemented
- [ ] Pickup code auto-detected from a real Amazon/FedEx email ❌ bug [#15](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/15)
- [ ] Mark as Used archives the source email ❌ not implemented
- [ ] Contact tag visually highlights emails from tagged sender ❌ not implemented
- [ ] Daily digest shows on dashboard home ❌ bug [#16](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/16)
- [ ] App deployed to public production URL ❌ issue [#10](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/10) open
- [ ] No critical bugs open at time of final delivery ❌ 6 blockers filed (issues #12–#17)

---

## Contract Terms

Per course requirements, both parties commit to:

**Proposer (Ting Li):**

- Review all PRs within 48 hours
- Provide specific, actionable written feedback on every review
- Respond to developer questions within 48 hours
- File bug reports with reproduction steps and screenshots

**Developer (John Huang):**

- Submit at least one PR per 2-week period
- Respond to all review comments within 48 hours
- Keep proposer informed of any blockers immediately
- Use agentic engineering tools (Cursor / Claude Code) for all implementation

Disputes are resolved by creating a GitHub Issue tagged
`escalation` for instructor review.

---

## Demo Day

**Proposer presents:**

- The problem and target user
- Revenue model and market opportunity
- Development story: what was built, what feedback was given,
  what changed through the process

**Developer presents:**

- System architecture (C4 diagram from ARCHITECTURE.md)
- Agentic engineering approach and AI tooling used
- Key technical decisions and tradeoffs

---

## Getting Started (for Developer)

### 1. Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. Run the SQL in `supabase/migrations/001_connected_accounts.sql` in the SQL Editor (creates `connected_accounts` for OAuth tokens).
3. **Authentication → URL configuration:** add site URL `http://localhost:3000` and redirect URL `http://localhost:3000/auth/callback` (add your production URLs when deployed).
4. Copy **Project URL**, **anon** key (frontend), **service_role** key (backend only), and **JWT Secret** (Settings → API → JWT Settings) for env files below.

### 2. Google Cloud (Gmail OAuth)

1. Enable **Gmail API** for the project.
2. OAuth consent screen (External test users as needed).
3. Create **OAuth 2.0 Client ID** (Web application).  
   **Authorized redirect URI** must exactly match `GMAIL_REDIRECT_URI`, e.g. `http://127.0.0.1:8000/auth/gmail/callback` (local) and your Railway API URL in production.

### 3. Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — use Supabase service_role + JWT secret (not anon key)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the interactive API.

### 4. Frontend (Next.js 14)

```bash
cd frontend
npm install
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL to the backend, e.g. http://127.0.0.1:8000
npm run dev
```

### Running AI quality tests

```bash
RUN_AI_QUALITY_TESTS=1 pytest backend/tests/ai_quality/
```

Estimated cost: about $0.20 per run.

### Cost monitoring

```sql
SELECT date_trunc('day', created_at), sum(cost_usd)
FROM ai_usage
GROUP BY 1
ORDER BY 1 DESC;
```

Visit `http://localhost:3000` → **Sign in** (magic link) → **Connect Gmail** → **Fetch recent emails** (expects ≥10 messages in the mailbox for the full acceptance check).

### 5. Deploy (skeleton)

- **Vercel:** import the repo, set **Root Directory** to `frontend`, add the same env vars as `.env.local`, set `NEXT_PUBLIC_API_URL` to your Railway API URL.
- **Railway:** new service from `backend/`, set variables from `backend/.env.example`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT` (see `Procfile`). Set `FRONTEND_URL` and `GMAIL_REDIRECT_URI` to the production callback URL.

**Backend `.env` (see `backend/.env.example`):**

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
# SUPABASE_JWT_SECRET — only if tokens use legacy HS256; leave blank for Supabase “JWT Signing Keys” (ECC)
SUPABASE_JWT_SECRET=
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REDIRECT_URI=
FRONTEND_URL=
OPENAI_API_KEY=<openai_api_key>
```

The API verifies browser sessions by reading the JWT `alg` header: **ES256/RS256** tokens are checked against Supabase JWKS (`/auth/v1/.well-known/jwks.json`); **HS256** tokens still use `SUPABASE_JWT_SECRET`.

**Frontend `.env.local` (see `frontend/.env.example`):**

```
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=
```

### Migrations

The SQL migrations live in `backend/supabase/migrations/`. To print all migrations in order (useful for pasting into Supabase SQL Editor):

```bash
make migrations
# or directly:
python backend/scripts/print_migrations.py
```

To apply migrations, paste the output into the **Supabase SQL Editor** for your project, or run it against your local Postgres instance.

---

## Production URLs

Set these after Vercel and Railway finish deploying:

| Surface | URL |
| ------- | --- |
| Frontend | `https://<vercel-url>` |
| Backend API | `https://<railway-url>` |
| Healthcheck | `https://<railway-url>/health` |

Run the production smoke test with:

```bash
API_URL=https://<railway-url> FRONTEND_URL=https://<vercel-url> ./scripts/smoke.sh
```

## Demo Prerequisites

Use a fresh Gmail account dedicated to the demo. Stage the mailbox before connecting it to InboxIQ:

- 1 interview invite or recruiter scheduling email with a clear reply deadline.
- 1 Amazon Locker or pickup-code email.
- 1 email from a sender that will be tagged as Professor, Friend, Recruiter, or a custom contact.
- 30 miscellaneous emails: newsletters, receipts, account updates, shipping notices, and low-priority promotions.

For graders and demo viewers: Google may show a "Google hasn't verified this app" warning while the OAuth consent screen is in Testing mode. This is expected for a class project. Click **Advanced** then **Continue** with a test-user email.

## Production Setup Checklist

### Vercel

- Create a new project from the `frontend/` root.
- Framework preset: Next.js.
- Environment variables:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - `NEXT_PUBLIC_API_URL=https://<railway-url>`
  - `NEXT_PUBLIC_SENTRY_DSN` optional
- Do not add `SUPABASE_SERVICE_ROLE_KEY` to Vercel.

### Railway

- Create a new service from the `backend/` root.
- Start command comes from `backend/Procfile`.
- Runtime is pinned by `backend/runtime.txt`.
- Environment variables:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_JWT_SECRET` only for legacy HS256 tokens, otherwise blank
  - `GMAIL_CLIENT_ID`
  - `GMAIL_CLIENT_SECRET`
  - `GMAIL_REDIRECT_URI=https://<railway-url>/auth/gmail/callback`
  - `OAUTH_STATE_SECRET` random 32+ character string
  - `OPENAI_API_KEY`
  - `FRONTEND_URL=https://<vercel-url>`
  - `ALLOWED_ORIGINS=https://<vercel-url>,http://localhost:3000`
  - `ENVIRONMENT=production`
  - `LOG_LEVEL=info`
  - `GIT_SHA` set from `$RAILWAY_GIT_COMMIT_SHA` in the build/deploy environment
  - `SENTRY_DSN` optional

### Google Cloud Console

- OAuth 2.0 Client -> Authorized redirect URIs:
  - `https://<railway-url>/auth/gmail/callback`
  - keep `http://localhost:8000/auth/gmail/callback` for development
- OAuth consent screen:
  - Testing mode is acceptable for this class project.
  - Add demo viewer Gmail addresses to the **Test users** list.

### Supabase

- Apply all migrations in `backend/supabase/migrations/` to the production project, currently `001` through `016`.
- Authentication -> URL Configuration:
  - Site URL: `https://<vercel-url>`
  - Redirect URLs:
    - `https://<vercel-url>/auth/callback`
    - `http://localhost:3000/auth/callback`

## Production Verification

After deployment:

1. Run `scripts/smoke.sh` against production and confirm it passes.
2. Run `backend/supabase/tests/test_rls.sql` in the production Supabase SQL editor and confirm all adversarial checks fail correctly.
3. Open production frontend in an incognito browser.
4. Sign in with a magic link and confirm it redirects to the production URL, not localhost.
5. Connect Gmail and confirm the OAuth callback redirects to `/settings` with the success toast.
6. Trigger `POST /accounts/{id}/sync` and confirm at least 10 emails appear in `/inbox`.
7. Wait 60-90 seconds for the AI worker and confirm triage badges and summaries appear.
8. Switch context from Daily to Job Hunting and confirm retriage updates the inbox.
9. Visit `/packages` and confirm pickup codes appear when present in the mailbox.
10. Visit `/contacts`, add a tag, then confirm the badge appears in `/inbox`.
11. Visit `/` and confirm the digest, deadlines, and pickup strip render.
12. Open DevTools Console on every page and confirm zero red errors.
13. Sign out and confirm protected routes redirect to `/auth/sign-in`.

## Troubleshooting

| Symptom | Fix |
| ------- | --- |
| Magic link redirects to localhost | Update Supabase Authentication -> URL Configuration so the Site URL and Redirect URLs point at Vercel. |
| OAuth callback `redirect_uri_mismatch` | In Google Cloud Console, make the authorized redirect URI exactly match `GMAIL_REDIRECT_URI`. |
| 401 on every API call | Check frontend `NEXT_PUBLIC_API_URL` and backend `ALLOWED_ORIGINS`; both must reference the production frontend/backend URLs exactly. |
| AI processing stuck | Check `OPENAI_API_KEY`, inspect `ai_usage` for recent activity, then check `ai_attempts` on stuck emails. |
| Scheduler not running | Railway must run a continuous service, not a cron-only job; confirm the worker process is live. |
