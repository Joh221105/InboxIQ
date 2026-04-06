# ARCHITECTURE.md — InboxIQ

## Overview

This document defines the initial architectural approach for InboxIQ — 
an AI-powered unified email management platform. It covers the data model, 
tech stack justification, and the agentic engineering plan for the AI 
pipeline.

---

## System Architecture Overview

| Decision | Choice | Reason |
|---|---|---|
| Frontend framework | Next.js 14 | SSR for fast initial load, zero-config Vercel deploy |
| Backend language | Python / FastAPI | Native AI ecosystem, async-first |
| AI call structure | Multi-step conditional pipeline | Better accuracy, lower token cost than single mega-prompt |
| Triage prompts | Static per context mode | Consistent, testable, cache-friendly |
| Email storage | body_preview only (2000 chars) | Prevents database bloat at scale |
| Re-triage scope | Last 100 unread emails only | Balances freshness with API cost |
| Sync strategy | Polling (15 min) + on-open | Simpler than push notifications for MVP |
| Token security | OAuth tokens in JSONB, server-side only | Never exposed to frontend |
| Data isolation | Row-level security in Supabase | Enforced at DB level, not just app level |


InboxIQ is structured as a three-layer system:

1. **Frontend** — A Next.js web app the user interacts with directly
2. **Backend** — A FastAPI server that orchestrates email syncing, 
   AI processing, and database operations
3. **AI Pipeline** — An agentic processing layer that runs on every 
   incoming email and on-demand when the user switches context

These three layers communicate as follows:

```
User Browser
     │
     ▼
Next.js Frontend (Vercel)
     │  REST API calls
     ▼
FastAPI Backend (Railway)
     │                    │
     ▼                    ▼
Supabase DB          OpenAI GPT-4o
(PostgreSQL)         AI Pipeline
     │
     ▼
Gmail API
(OAuth 2.0)
```

---

## Tech Stack Justification

### Frontend — Next.js 14 + Tailwind CSS + shadcn/ui

**Why Next.js 14:**
Next.js is chosen over plain React or Vite for three specific reasons 
relevant to InboxIQ. First, server-side rendering allows the dashboard 
and inbox to load with data already populated — critical for an app 
where the user expects to see their emails immediately on open, not 
after a loading spinner. Second, Next.js API routes provide a clean 
place to handle OAuth callbacks from Gmail without needing a separate 
backend endpoint for that specific flow.

**Why Tailwind CSS + shadcn/ui:**
Tailwind provides the utility-first styling needed to build a dense, 
information-rich UI like an email client without fighting a component 
library's opinions. shadcn/ui sits on top of Tailwind and provides 
pre-built, accessible components (cards, tabs, badges, dialogs) that 
match the clean, minimal aesthetic described in the spec. Together they 
allow rapid iteration on UI without writing CSS from scratch.

---

### Backend — FastAPI (Python)

**Why FastAPI over Node.js/Express:**
The backend is the most AI-heavy layer in InboxIQ. FastAPI is chosen 
because Python is the native language of the AI/ML ecosystem. The 
OpenAI Python SDK, Gmail API client libraries, and any future ML 
tooling all have first-class Python support. FastAPI specifically is 
chosen over Flask or Django because it is async-native — essential for 
a backend that needs to process batches of emails concurrently without 
blocking. Its built-in request validation via Pydantic also reduces 
boilerplate when handling complex OAuth token payloads and email 
sync responses.

---

### Database — Supabase (PostgreSQL)

**Why Supabase:**
Supabase provides three things in one: a managed PostgreSQL database, 
a built-in authentication system, and row-level security policies. 
For InboxIQ, row-level security is not optional — it is a hard 
requirement that users can never access another user's emails, tokens, 
or contact tags. Supabase enforces this at the database level rather 
than relying solely on application-level checks, which is the correct 
architectural choice for a multi-user email product handling sensitive 
OAuth tokens.

PostgreSQL specifically supports the JSONB column type used for 
storing OAuth tokens, which need to be read and updated atomically 
on every token refresh without a schema migration.

---

### AI — OpenAI GPT-4o

**Why GPT-4o:**
GPT-4o is chosen for four reasons. First, it has strong instruction 
following for structured output tasks — critical for deadline 
extraction, where the model needs to reliably return a date in a 
parseable format rather than a prose sentence. Second, its context 
window is large enough to handle full email bodies without aggressive 
truncation in most real-world cases. Third, it supports JSON mode, 
which allows the triage pipeline to request structured responses 
(category, summary, deadline, pickup code) in a single API call 
rather than four separate calls. Fourth, it has the best 
cost-to-performance ratio for high-frequency, per-email processing 
at the volume InboxIQ requires.

---

### Email — Gmail API (OAuth 2.0)

**Why Gmail-only for MVP:**
Microsoft Graph API (Outlook) is a significantly more complex 
integration with different token formats, rate limits, and 
permission scopes. Limiting the MVP to Gmail allows the team 
to ship a polished, production-quality integration rather than 
two half-finished ones. Outlook support is explicitly scoped 
to V2 in the spec.

---

## Data Model

The following expands on the spec's schema with architectural 
annotations explaining key design decisions.

---

### `users`
```sql
CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email           TEXT UNIQUE NOT NULL,
  default_context TEXT NOT NULL DEFAULT 'Daily',
  created_at      TIMESTAMPTZ DEFAULT now()
);
```
**Notes:**
- `default_context` is stored here so the dashboard loads 
  immediately with the correct triage mode without an 
  extra round trip
- Row-level security policy: users can only SELECT, UPDATE 
  their own row where `id = auth.uid()`

---

### `connected_accounts`
```sql
CREATE TABLE connected_accounts (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
  email_address TEXT NOT NULL,
  provider      TEXT NOT NULL CHECK (provider IN ('gmail', 'outlook')),
  oauth_token   JSONB NOT NULL,
  color         TEXT NOT NULL,
  last_synced   TIMESTAMPTZ,
  created_at    TIMESTAMPTZ DEFAULT now()
);
```
**Notes:**
- `oauth_token` is JSONB storing `{ access_token, refresh_token, 
  expires_at }` as a single atomic unit — updated together on 
  every refresh to avoid partial update bugs
- `last_synced` is used by the sync scheduler to determine 
  the fetch window on each sync cycle
- `color` is assigned from a fixed palette of 8 visually 
  distinct colors on account creation, cycling if the user 
  connects more than 8 accounts
- `ON DELETE CASCADE` ensures all emails and data are 
  cleaned up when an account is disconnected

---

### `emails`
```sql
CREATE TABLE emails (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id         UUID REFERENCES connected_accounts(id) 
                     ON DELETE CASCADE,
  external_id        TEXT NOT NULL,
  sender_email       TEXT NOT NULL,
  subject            TEXT,
  body_preview       TEXT,
  received_at        TIMESTAMPTZ NOT NULL,
  ai_summary         TEXT,
  triage_category    TEXT CHECK (
                       triage_category IN (
                         'action_required', 
                         'worth_reading', 
                         'auto_archive'
                       )
                     ),
  triage_context     TEXT,
  deadline_extracted DATE,
  action_items       JSONB,
  is_pickup_code     BOOLEAN DEFAULT false,
  pickup_code        TEXT,
  pickup_expiry      DATE,
  pickup_used        BOOLEAN DEFAULT false,
  is_archived        BOOLEAN DEFAULT false,
  ai_processed       BOOLEAN DEFAULT false,
  created_at         TIMESTAMPTZ DEFAULT now(),
  UNIQUE(account_id, external_id)
);
```
**Notes:**
- `external_id` + `account_id` unique constraint prevents 
  duplicate emails if the sync pipeline runs overlapping 
  windows
- `body_preview` stores the first 2000 characters of the 
  email body — enough for AI processing without storing 
  full email bodies in the database, which would grow 
  rapidly at scale
- `triage_context` stores which context mode was active 
  when the email was triaged, so the system knows when 
  a re-triage is needed after a context switch
- `action_items` is JSONB storing an array of extracted 
  action strings — e.g. `["Complete OA by Nov 15", 
  "Reply to confirm interview time"]`
- `ai_processed` is a processing flag used by the 
  background job to identify emails in the queue that 
  have not yet been through the AI pipeline

**Indexes:**
```sql
CREATE INDEX idx_emails_account_received 
  ON emails(account_id, received_at DESC);
CREATE INDEX idx_emails_triage 
  ON emails(triage_category, is_archived);
CREATE INDEX idx_emails_pickup 
  ON emails(is_pickup_code, pickup_used) 
  WHERE is_pickup_code = true;
CREATE INDEX idx_emails_unprocessed 
  ON emails(ai_processed) 
  WHERE ai_processed = false;
```

---

### `contact_tags`
```sql
CREATE TABLE contact_tags (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
  identifier   TEXT NOT NULL,
  tag          TEXT NOT NULL,
  custom_label TEXT,
  color        TEXT NOT NULL,
  created_at   TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, identifier)
);
```
**Notes:**
- `identifier` accepts either a full email address 
  (`jane@uw.edu`) or a domain prefix (`@uw.edu`) — 
  the matching logic in the backend handles both patterns
- The unique constraint on `(user_id, identifier)` prevents 
  duplicate tags for the same contact

---

### Row-Level Security Policies

All tables have RLS enabled. The pattern is consistent:

```sql
-- Example for emails (applied similarly to all tables)
ALTER TABLE emails ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access their own emails"
ON emails
FOR ALL
USING (
  account_id IN (
    SELECT id FROM connected_accounts 
    WHERE user_id = auth.uid()
  )
);
```

---

## Agentic Engineering Plan

### What "Agentic" Means for InboxIQ

InboxIQ's AI pipeline is agentic in a narrow but meaningful sense: 
rather than a single prompt producing a single output, the pipeline 
involves a sequence of decisions — classify, then conditionally 
extract, then conditionally parse — where each step's output 
determines whether the next step runs. This keeps token usage low 
and latency acceptable for real-time email sync.

---

### The Email Processing Pipeline

Every incoming email passes through the following pipeline. 
Steps run sequentially. Each step is a separate function but 
all run within a single background task per email.

```
New Email Arrives
      │
      ▼
Step 1: Pre-filter
(rule-based, no AI)
      │
      ├─ Is sender in user's contact_tags? → Tag badge, 
      │  flag for priority treatment regardless of triage
      │
      ├─ Subject matches pickup code pattern? → Skip to 
      │  Step 4 (pickup extraction) directly
      │
      └─ Proceed to Step 2
      │
      ▼
Step 2: AI Triage Call
(single GPT-4o call, JSON mode)
Input:  sender, subject, body_preview, current_context
Output: {
  category: "action_required" | "worth_reading" | "auto_archive",
  summary: "one-line plain English summary",
  has_deadline: boolean,
  has_action_items: boolean,
  is_pickup_code: boolean
}
      │
      ├─ if has_deadline = true → Step 3a
      ├─ if has_action_items = true → Step 3b  
      ├─ if is_pickup_code = true → Step 4
      └─ else → Step 5 (save and done)
      │
      ▼
Step 3a: Deadline Extraction (conditional)
(separate GPT-4o call, JSON mode)
Input:  body_preview
Output: { deadline: "YYYY-MM-DD", deadline_text: "raw string" }

Step 3b: Action Item Extraction (conditional)
(separate GPT-4o call, JSON mode)  
Input:  body_preview
Output: { action_items: ["string", "string"] }
      │
      ▼
Step 4: Pickup Code Extraction (conditional)
(separate GPT-4o call, JSON mode)
Input:  subject, body_preview
Output: {
  pickup_code: "string",
  pickup_expiry: "YYYY-MM-DD" | null,
  locker_location: "string" | null
}
      │
      ▼
Step 5: Write to Database
All extracted fields written to emails table in one 
atomic update. ai_processed set to true.
```

---

### Why Separate Calls for Each Extraction Step

Combining all extraction into one prompt produces unreliable 
structured output — the model tends to hallucinate deadline dates 
or action items when none exist if asked to fill every field 
simultaneously. By gating Steps 3 and 4 behind boolean flags 
from Step 2, the system only asks extraction questions when the 
triage call has already confirmed there is something to extract. 
This improves accuracy and reduces unnecessary token spend on 
emails that have no deadline or pickup code.

---

### Context-Aware Triage Prompts

The system prompt for Step 2 changes based on the user's current 
context mode. Each context mode has a dedicated static system 
prompt stored as a constant in the backend. This is a key 
architectural decision — static prompts maximize consistency 
and make behavior predictable and testable.

**Structure of the triage system prompt:**
```
You are an email triage assistant. The user is currently in 
[CONTEXT_MODE] mode.

In this mode, classify emails as follows:
- action_required: [context-specific definition]
- worth_reading: [context-specific definition]  
- auto_archive: [context-specific definition]

Respond only in JSON with this exact schema:
{
  "category": "action_required" | "worth_reading" | "auto_archive",
  "summary": "one sentence, max 15 words",
  "has_deadline": boolean,
  "has_action_items": boolean,
  "is_pickup_code": boolean
}
```

Four versions of this prompt exist — one per context mode — 
stored as constants. No dynamic content is injected into the 
system prompt. User-specific data (sender, subject, body) is 
passed only in the user message.

---

### Re-Triage on Context Switch

When a user switches context mode, the following happens:

1. Backend receives a PATCH request to `/users/context` with 
   the new context value
2. User's `default_context` is updated in the database
3. A background task is queued to re-triage the last 100 
   unread, non-archived emails for this user
4. Re-triage runs the Step 2 triage call only (not 
   extraction steps — deadlines and pickup codes do not 
   change with context)
5. Updated triage categories written back to the emails table
6. Frontend polls for completion or receives a WebSocket 
   push that re-triage is done and refreshes the inbox view

Re-triage is rate-limited to once per 60 seconds per user 
to prevent rapid context switching from triggering 
excessive API calls.

---

### Daily Digest Generation

The daily digest is generated once per user per day, 
triggered on first app open after midnight local time.

```
Input to GPT-4o:
- All action_required emails from the last 24 hours 
  (subject + ai_summary + deadline if present)
- All upcoming deadlines in the next 7 days

Output:
- Top 3-5 action items summarized in one line each
- Ordered by deadline proximity, then by recency
```

The digest is cached in the user's session for the day 
and regenerated on the next day's first open.

---

### Email Sync Schedule

Emails are not streamed in real time (Gmail push 
notifications are a V2 feature). Instead, a polling 
sync runs on the following schedule:

- **On app open:** Sync all connected accounts, 
  fetch emails since `last_synced`
- **Background polling:** Every 15 minutes per 
  connected account via a scheduled task on Railway

The sync pipeline:
```
1. Read last_synced timestamp for this account
2. Call Gmail API: fetch all message IDs since last_synced
3. For each new message ID:
   a. Fetch full message (subject, sender, body preview)
   b. Write raw email to emails table with ai_processed = false
4. Update last_synced to now()
5. Background AI pipeline picks up all emails where 
   ai_processed = false and processes them in batches of 10
```

Batching AI processing at step 5 rather than inline with 
the sync allows the sync to complete fast and the AI 
processing to happen asynchronously without blocking 
the user's inbox from loading.

---

### Error Handling Strategy

| Error Type | Handling |
|---|---|
| Gmail API rate limit | Exponential backoff, max 3 retries |
| OpenAI API timeout | Mark email with `ai_processed = false`, retry on next sync cycle |
| OpenAI API error (5xx) | Display email without summary, show "AI unavailable" badge |
| OAuth token expired | Auto-refresh using refresh_token before retrying |
| OAuth refresh fails | Mark account as disconnected, prompt user to reconnect |
| Email body too long | Truncate to first 2000 characters, note truncation in summary |
| Non-English email | Model detects language and summarizes in English |
| Image-only email | Flag as "Content not readable — manual review suggested" |

