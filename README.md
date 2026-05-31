# InboxIQ 📬

> AI-Powered Unified Email Management App

---

## Live Deployment

| Surface     | URL                                                                                                  |
| ----------- | ---------------------------------------------------------------------------------------------------- |
| Frontend    | <https://tingting-silk.vercel.app>                                                                   |
| Backend API | <https://inboxiq-api-production.up.railway.app>                                                      |
| Healthcheck | <https://inboxiq-api-production.up.railway.app/health>                                               |

> The Google OAuth consent screen is in **Testing** mode for this class
> project. Your Gmail address must be added to the **Test users** list
> in Google Cloud Console before "Connect Gmail" will succeed — contact
> the proposer (Ting Li) or developer (John Huang) to be added.

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

> **Final delivery completed: May 30, 2026.**
> All mid-point blocker bugs (#12–#17) and open feature issues (#4–#10)
> have been resolved. App is deployed to production and demo-ready.

| Milestone             | Deadline             | Status | Required Progress                                                                                                                             | Acceptance Gate                                                | Notes |
| --------------------- | -------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ----- |
| ✅ **Check-in 1**     | End of Week 1, Day 3 | **Met (late)** | OAuth login working for Gmail; emails fetched and stored in DB; project deployed to staging URL; ARCHITECTURE.md submitted | Proposer reviews Architecture PR within 48 hours | ARCHITECTURE.md merged (PR #2). Gmail OAuth merged May 2 (PR #11). Emails are now persisted to the `emails` table via the sync pipeline. |
| ✅ **Check-in 2**     | End of Week 1, Day 6 | **Met (late)** | AI triage pipeline working (3-category classification + summary); context mode switcher functional; unified inbox page live on staging | Proposer conducts acceptance test on inbox triage accuracy | AI triage pipeline live (`backend/app/services/triage.py`); context switcher renders triage per mode; `/inbox` page deployed. Bugs [#12](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/12), [#13](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/13), [#14](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/14) closed. |
| ✅ **Check-in 3**     | End of Week 2, Day 3 | **Met** | Package tracker complete with auto-detection and mark-as-used; deadline extraction working; contact tagging functional; all MVP issues closed | Proposer files bug reports; developer resolves within 48 hours | `/packages` ships with auto-detected pickup codes and Mark as Used. Deadline extraction surfaces on dashboard. `/contacts` tagging highlights senders in `/inbox`. Bugs [#15](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/15), [#16](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/16), [#17](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/17) closed. Issues #4–#10 closed. |
| 🏁 **Final Delivery** | End of Week 2        | **Delivered** | All MVP features polished and deployed to production URL; README updated; tests passing; demo-ready                                           | Final acceptance test by proposer; GIX Bucks paid on approval  | Frontend deployed at <https://tingting-silk.vercel.app>; backend at <https://inboxiq-api-production.up.railway.app>. All 6 blocker bugs and 7 feature issues closed. Ready for proposer acceptance test. |

### Final Status (May 30, 2026)

**What is working in production:**
- Supabase magic-link authentication (`/auth/sign-in`)
- Gmail OAuth 2.0 flow with token storage in `connected_accounts`
- Email sync pipeline persisting messages (subject, sender, body, snippet) to the `emails` table
- AI triage pipeline: 3-category classification (Action Required / Worth Reading / Auto-Archive) + summary + deadline extraction
- Context mode switcher (Daily / Job Hunting / Shopping / School) with per-mode retriage
- Unified `/inbox` page with triage badges and AI summaries
- `/packages` pickup-code tracker with auto-detection and Mark as Used
- `/contacts` tagging with sender highlights in `/inbox`
- `/` dashboard with daily digest, deadlines, and pickup strip
- Background scheduler + AI worker running continuously on Railway

**Mid-point blockers — all resolved:**

| Bug | Issue | Resolution |
| --- | ----- | ---------- |
| [#12](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/12) AI triage badges and summaries absent | #5 | ✅ Closed — triage pipeline shipped |
| [#13](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/13) Context mode switcher absent | #5 | ✅ Closed — switcher live on `/inbox` |
| [#14](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/14) Email body not fetched; no OpenAI client | #5 #6 #8 | ✅ Closed — body fetched in sync; OpenAI client in `app/services/openai_client.py` |
| [#15](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/15) Package tracker page missing | #8 | ✅ Closed — `/packages` page deployed |
| [#16](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/16) Dashboard home page missing | #9 | ✅ Closed — `/` dashboard deployed |
| [#17](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/17) `emails` and `contact_tags` DB tables not created | #4–#8 | ✅ Closed — migrations 001–021 applied |

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
- [x] All emails displayed in unified inbox with triage badges ✅ bug [#12](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/12) closed
- [x] Switching context mode visibly changes triage results ✅ bug [#13](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/13) closed
- [x] AI summary visible on every email card ✅ bug [#14](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/14) closed
- [x] At least 1 deadline correctly extracted from a real email ✅ deadline extraction shipped
- [x] Pickup code auto-detected from a real Amazon/FedEx email ✅ bug [#15](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/15) closed
- [x] Mark as Used archives the source email ✅ `/packages` Mark as Used live
- [x] Contact tag visually highlights emails from tagged sender ✅ `/contacts` tagging live
- [x] Daily digest shows on dashboard home ✅ bug [#16](https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues/16) closed
- [x] App deployed to public production URL ✅ <https://tingting-silk.vercel.app>
- [x] No critical bugs open at time of final delivery ✅ all 6 blockers (issues #12–#17) closed

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

## Running the App Locally

### Prerequisites

| Tool | Version |
| ---- | ------- |
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |

You also need accounts at [Supabase](https://supabase.com), [Google Cloud](https://console.cloud.google.com) (Gmail API), and [OpenAI](https://platform.openai.com).

---

### Step 1 — Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. **Apply all migrations** in `backend/supabase/migrations/` (001 through 021) into the Supabase SQL Editor.  
   Use the helper script to print them all in order:
   ```bash
   python backend/scripts/print_migrations.py
   ```
   Then paste the output into the **SQL Editor** in your Supabase dashboard.
3. **Authentication → URL configuration:**
   - Site URL: `http://localhost:3000`
   - Redirect URL: `http://localhost:3000/auth/callback`
4. Copy your keys for the env files below:
   - **Project URL** → `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL`
   - **anon key** → `NEXT_PUBLIC_SUPABASE_ANON_KEY` (frontend only)
   - **service_role key** → `SUPABASE_SERVICE_ROLE_KEY` (backend only — never exposed to frontend)
   - **JWT Secret** (Settings → API → JWT Settings) → `SUPABASE_JWT_SECRET`

---

### Step 2 — Google Cloud (Gmail OAuth)

1. Enable the **Gmail API** in your Google Cloud project.
2. Configure the OAuth consent screen (External, add test users as needed).
3. Create an **OAuth 2.0 Client ID** (Web application).
   - Add authorized redirect URI: `http://127.0.0.1:8000/auth/gmail/callback`
4. Copy **Client ID** → `GMAIL_CLIENT_ID` and **Client Secret** → `GMAIL_CLIENT_SECRET`.

---

### Step 3 — Backend (FastAPI)

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env
```

**`backend/.env` — required variables:**

```ini
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role_key>
SUPABASE_JWT_SECRET=<jwt_secret>        # leave blank for ECC/RS256 projects
GMAIL_CLIENT_ID=<oauth_client_id>
GMAIL_CLIENT_SECRET=<oauth_client_secret>
GMAIL_REDIRECT_URI=http://127.0.0.1:8000/auth/gmail/callback
OAUTH_STATE_SECRET=<random_32+_char_string>
OPENAI_API_KEY=<openai_api_key>
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=http://localhost:3000
```

```bash
# Start the API server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

> Interactive API docs: <http://127.0.0.1:8000/docs>

The background AI worker and email sync scheduler start automatically with the server.

---

### Step 4 — Frontend (Next.js 14)

```bash
cd frontend

# Install dependencies
npm install

# Copy and fill in environment variables
cp .env.example .env.local
```

**`frontend/.env.local` — required variables:**

```ini
NEXT_PUBLIC_SUPABASE_URL=https://<your-project>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon_key>
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

```bash
# Start the dev server
npm run dev
```

> App: <http://localhost:3000>

---

### Step 5 — First-run walkthrough

1. Open `http://localhost:3000`
2. **Sign in** via magic link (check your email)
3. Go to **Settings** → **Connect Gmail** → complete the OAuth flow
4. Trigger an initial sync: `POST /accounts/{id}/sync` from the API docs (or wait up to 60 s for the scheduler)
5. Visit **Inbox** — emails should appear with AI triage badges within ~90 s

---

### Running the Tests

**Backend (pytest):**

```bash
cd backend
source .venv/bin/activate

# Run the full test suite
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific module
pytest tests/services/test_triage.py -v
```

**Frontend (Vitest):**

```bash
cd frontend
npm test              # run all unit tests
npm run test:ui       # interactive watch mode
```

**Frontend (Playwright E2E):**

```bash
cd frontend
npx playwright install   # first time only
npx playwright test
```

**Backend AI quality tests** (cost ~$0.20/run, uses real OpenAI):

```bash
cd backend
RUN_AI_QUALITY_TESTS=1 pytest tests/ai_quality/
```

---

### Cost monitoring

```sql
SELECT date_trunc('day', created_at), sum(cost_usd)
FROM ai_usage
GROUP BY 1
ORDER BY 1 DESC;
```

---

### Step 6 — Deploy to Production

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

| Surface     | URL                                                          |
| ----------- | ------------------------------------------------------------ |
| Frontend    | <https://tingting-silk.vercel.app>                           |
| Backend API | <https://inboxiq-api-production.up.railway.app>              |
| Healthcheck | <https://inboxiq-api-production.up.railway.app/health>       |

Run the production smoke test with:

```bash
API_URL=https://inboxiq-api-production.up.railway.app \
FRONTEND_URL=https://tingting-silk.vercel.app \
./scripts/smoke.sh
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
  - `NEXT_PUBLIC_API_URL=https://inboxiq-api-production.up.railway.app`
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
  - `GMAIL_REDIRECT_URI=https://inboxiq-api-production.up.railway.app/auth/gmail/callback`
  - `OAUTH_STATE_SECRET` random 32+ character string
  - `OPENAI_API_KEY`
  - `FRONTEND_URL=https://tingting-silk.vercel.app`
  - `ALLOWED_ORIGINS=https://tingting-silk.vercel.app,http://localhost:3000`
  - `ENVIRONMENT=production`
  - `LOG_LEVEL=info`
  - `GIT_SHA` set from `$RAILWAY_GIT_COMMIT_SHA` in the build/deploy environment
  - `SENTRY_DSN` optional

### Google Cloud Console

- OAuth 2.0 Client -> Authorized redirect URIs:
  - `https://inboxiq-api-production.up.railway.app/auth/gmail/callback`
  - keep `http://localhost:8000/auth/gmail/callback` for development
- OAuth consent screen:
  - Testing mode is acceptable for this class project.
  - Add demo viewer Gmail addresses to the **Test users** list (Google Cloud Console → APIs & Services → OAuth consent screen → Test users).

### Supabase

- Apply all migrations in `backend/supabase/migrations/` to the production project, currently `001` through `021`.
- Authentication -> URL Configuration:
  - Site URL: `https://tingting-silk.vercel.app`
  - Redirect URLs:
    - `https://tingting-silk.vercel.app/auth/callback`
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
