# Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all bugs, missing features, and code quality issues surfaced in the May 25 2026 codebase audit.

**Architecture:** Fixes are grouped by layer (DB migrations → backend bugs → backend features → frontend bugs → frontend features). Each task is independently deployable. Tasks with no cross-dependencies can be parallelised. The database migration task (Task 1) must complete before any backend task that touches the emails table (Tasks 7, 8).

**Tech Stack:** FastAPI + Pydantic v2 + supabase-py (backend), Next.js 14 App Router + React Query + TypeScript strict (frontend), Supabase PostgreSQL (DB), pytest + pytest-asyncio + respx (backend tests), Vitest (frontend tests).

---

## File Map

| File | Action | Reason |
|---|---|---|
| `backend/supabase/migrations/013_pickup_used_at.sql` | Rename → `014_pickup_used_at.sql` | Duplicate number conflict |
| `backend/supabase/migrations/014_pickup_extras.sql` | Rename → `015_pickup_extras.sql` | Cascading renumber |
| `backend/supabase/migrations/015_contact_tag_on_emails.sql` | Rename → `016_contact_tag_on_emails.sql` | Cascading renumber |
| `backend/supabase/migrations/016_security_hardening.sql` | Rename → `017_security_hardening.sql` | Cascading renumber |
| `backend/supabase/migrations/017_user_settings.sql` | Rename → `018_user_settings.sql` | Cascading renumber |
| `backend/supabase/migrations/019_sender_name.sql` | Create | Add sender_name column |
| `backend/supabase/migrations/020_data_retention.sql` | Create | Add retention enforcement function |
| `backend/app/db/users.py` | Modify | Fix `.select()` on update_default_context |
| `backend/app/db/emails.py` | Modify | Fix plfts sanitization, add sender_name to upsert |
| `backend/app/models/email.py` | Modify | Add sender_name to ParsedEmail + Email |
| `backend/app/services/gmail_sync.py` | Modify | Parse and store sender display name |
| `backend/app/services/email_body.py` | Modify | Improved HTML sanitization |
| `backend/app/services/triage.py` | Modify | Force action_required for tagged contacts |
| `backend/app/services/contact_tags.py` | Modify | TTL eviction for JOBS dict |
| `backend/app/services/retriage.py` | Modify | TTL eviction for JOBS + _last_request_at |
| `backend/app/services/gmail_oauth.py` | Modify | TTL eviction for _refresh_locks |
| `backend/app/services/openai_client.py` | Modify | Enforce BATCH_COST_CAP_USD |
| `backend/app/tasks/ai_worker.py` | Modify | Wire cost cap per batch |
| `backend/app/tasks/scheduler.py` | Modify | Add nightly data-retention job |
| `backend/app/routers/contacts.py` | Modify | Add PATCH /contacts/{id} endpoint |
| `backend/app/db/contact_tags.py` | Modify | Add update_tag() helper |
| `backend/app/models/contact_tag.py` | Modify | Add ContactTagUpdate model |
| `backend/tests/db/test_emails.py` | Modify | Tests for sanitized search + sender_name |
| `backend/tests/routers/test_contacts.py` | Modify | Tests for PATCH /contacts/{id} |
| `backend/tests/services/test_triage.py` | Modify | Tests for tagged-contact override |
| `backend/tests/services/test_email_body.py` | Modify | Tests for improved sanitization |
| `frontend/types/index.ts` | Modify | Add sender_name field to Email type |
| `frontend/lib/queries/context-switch.ts` | Modify | Poll /jobs/{job_id} after context switch |
| `frontend/components/inbox/contact-tag-badge.tsx` | Modify | Use Next.js Link |
| `frontend/components/inbox/email-card.tsx` | Modify | Show sender_name |
| `frontend/components/inbox/email-detail-panel.tsx` | Modify | Show sender_name |
| `frontend/app/layout.tsx` | Modify | Active nav link styling |
| `frontend/app/page.tsx` | Modify | Time-of-day greeting |
| `frontend/tests/inbox/EmailCard.test.tsx` | Modify | Tests for sender_name display |

---

## Task 1: Fix Duplicate Migration Number 013

**Files:**
- Rename: `backend/supabase/migrations/013_pickup_used_at.sql` → `014_pickup_used_at.sql`
- Rename: `backend/supabase/migrations/014_pickup_extras.sql` → `015_pickup_extras.sql`
- Rename: `backend/supabase/migrations/015_contact_tag_on_emails.sql` → `016_contact_tag_on_emails.sql`
- Rename: `backend/supabase/migrations/016_security_hardening.sql` → `017_security_hardening.sql`
- Rename: `backend/supabase/migrations/017_user_settings.sql` → `018_user_settings.sql`

**Context:** Two files both named `013_*` exist. Any migration runner ordering by filename will process them in an undefined order or fail. All files from 014 onward need cascading renumbers to keep the sequence gapless.

- [ ] **Step 1: Rename all five files**

```bash
cd backend/supabase/migrations
mv 013_pickup_used_at.sql 014_pickup_used_at.sql
mv 014_pickup_extras.sql 015_pickup_extras.sql
mv 015_contact_tag_on_emails.sql 016_contact_tag_on_emails.sql
mv 016_security_hardening.sql 017_security_hardening.sql
mv 017_user_settings.sql 018_user_settings.sql
```

- [ ] **Step 2: Verify sequence is gapless**

```bash
ls backend/supabase/migrations/*.sql | sort
```

Expected output (in order): `001_users.sql`, `002_connected_accounts.sql`, `003_emails.sql`, `004_contact_tags.sql`, `005_auth_trigger.sql`, `006_color_palette.sql`, `007_schema_alignment.sql`, `008_last_synced_is_archived.sql`, `009_upsert_email_fn.sql`, `010_email_search.sql`, `011_ai_usage.sql`, `012_ai_attempts.sql`, `013_daily_digests.sql`, `014_pickup_used_at.sql`, `015_pickup_extras.sql`, `016_contact_tag_on_emails.sql`, `017_security_hardening.sql`, `018_user_settings.sql`.  
No two files should share a number prefix.

- [ ] **Step 3: Commit**

```bash
git add backend/supabase/migrations/
git commit -m "fix(migrations): resolve duplicate 013 number, renumber 014-018 (#audit)"
```

---

## Task 2: Fix `update_default_context` Missing `.select()`

**Files:**
- Modify: `backend/app/db/users.py`
- Test: `backend/tests/db/test_users.py`

**Context:** `update_default_context` calls `.update().eq().execute()` without `.select()`. In supabase-py, `.execute()` without `.select()` returns `data = []`, so `rows[0]` is unreachable and the function silently returns `None`. While the current callers discard the return value, this is a latent bug.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/db/test_users.py`:

```python
@pytest.mark.asyncio
async def test_update_default_context_returns_updated_user() -> None:
    """update_default_context must return the user with the new context value."""
    from app.db.users import update_default_context

    user_id = uuid4()
    captured_select = []

    class _Result:
        data = [
            {
                "id": str(user_id),
                "email": "user@example.com",
                "default_context": "Job Hunting",
                "notification_tag_preferences": {},
                "data_retention_days": None,
                "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
            }
        ]

    class _Chain:
        def update(self, _changes):
            return self

        def eq(self, *_args):
            return self

        def select(self, fields):
            captured_select.append(fields)
            return self

        def execute(self):
            return _Result()

    class _Client:
        def table(self, _name):
            return _Chain()

    from unittest.mock import patch

    with patch("app.db.users.get_service_client", return_value=_Client()):
        user = await update_default_context(user_id, "Job Hunting")

    assert user.default_context == "Job Hunting"
    assert captured_select, "select() must be called so Supabase returns the updated row"
```

- [ ] **Step 2: Run test — expect failure**

```bash
cd backend && python -m pytest tests/db/test_users.py::test_update_default_context_returns_updated_user -v
```

Expected: `FAILED` — `assert captured_select` fails because `.select()` is never called.

- [ ] **Step 3: Fix `update_default_context` in `backend/app/db/users.py`**

Replace the existing `update_default_context` function:

```python
async def update_default_context(user_id: UUID, context: str) -> User:
    def _update() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("users")
            .update({"default_context": context})
            .eq("id", str(user_id))
            .select("*")          # ← required: without this, data is []
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    data = await asyncio.to_thread(_update)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**data)
```

- [ ] **Step 4: Run test — expect pass**

```bash
cd backend && python -m pytest tests/db/test_users.py::test_update_default_context_returns_updated_user -v
```

Expected: `PASSED`

- [ ] **Step 5: Run full db tests**

```bash
cd backend && python -m pytest tests/db/test_users.py -v
```

All should pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/db/users.py backend/tests/db/test_users.py
git commit -m "fix(db): add .select() to update_default_context so it returns updated row (#audit)"
```

---

## Task 3: Sanitize Full-Text Search Input Before Passing to `plfts`

**Files:**
- Modify: `backend/app/db/emails.py`
- Test: `backend/tests/db/test_emails.py`

**Context:** `plfts(english)` passes the value directly to PostgreSQL's `phraseto_tsquery()`. Characters like `'`, `&`, `|`, `!`, `(`, `)` are valid tsquery operators and will cause a Postgres syntax error returned as a 500. The input must be sanitized to plain words-only before the query.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/db/test_emails.py` (find the existing file and append):

```python
from app.db.emails import _sanitize_fts_input


def test_sanitize_fts_strips_tsquery_operators() -> None:
    assert _sanitize_fts_input("') OR 1=1 --") == "OR 1 1"


def test_sanitize_fts_keeps_alphanumeric_and_spaces() -> None:
    assert _sanitize_fts_input("amazon order") == "amazon order"


def test_sanitize_fts_strips_special_chars() -> None:
    assert _sanitize_fts_input("hello!world&foo|bar") == "hello world foo bar"


def test_sanitize_fts_none_returns_none() -> None:
    assert _sanitize_fts_input(None) is None


def test_sanitize_fts_empty_string_returns_none() -> None:
    assert _sanitize_fts_input("   ") is None
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd backend && python -m pytest tests/db/test_emails.py::test_sanitize_fts_strips_tsquery_operators -v
```

Expected: `FAILED` — `ImportError: cannot import name '_sanitize_fts_input'`

- [ ] **Step 3: Add `_sanitize_fts_input` and wire it into `list_emails`**

In `backend/app/db/emails.py`, add the helper near the top (after imports):

```python
import re

def _sanitize_fts_input(value: str | None) -> str | None:
    """Strip characters that are PostgreSQL tsquery operators.
    
    phraseto_tsquery() rejects '&', '|', '!', '(', ')', '<', '>', '"', "'"
    and single-character tokens. We keep only word characters and spaces,
    then collapse extra whitespace. Returns None if nothing remains.
    """
    if not value:
        return None
    cleaned = re.sub(r"[^\w\s]", " ", value)   # strip non-word non-space chars
    collapsed = " ".join(cleaned.split())        # collapse whitespace
    return collapsed or None
```

Then update the `if filters.search:` block in `list_emails._fetch()`:

```python
if filters.search:
    safe_search = _sanitize_fts_input(filters.search)
    if safe_search:
        q = q.filter("search_tsv", "plfts(english)", safe_search)
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd backend && python -m pytest tests/db/test_emails.py -k "sanitize" -v
```

Expected: all 5 `test_sanitize_fts_*` pass.

- [ ] **Step 5: Run full db/email tests**

```bash
cd backend && python -m pytest tests/db/test_emails.py -v
```

All should pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/db/emails.py backend/tests/db/test_emails.py
git commit -m "fix(db): sanitize FTS input before plfts to prevent tsquery syntax errors (#audit)"
```

---

## Task 4: Improve HTML Body Sanitization

**Files:**
- Modify: `backend/app/services/email_body.py`
- Test: `backend/tests/routers/test_email_body.py` (already exists — extend it)

**Context:** `sanitize_body_html` only removes `<script>` tags. It must also remove `<style>`, `<link>`, `<meta>`, `<base>`, and all inline event handlers (`onclick`, `onerror`, `onload`, etc.) to prevent CSS-based tracking and exfiltration. The detail-panel `iframe` uses `sandbox=""` (no scripts), but `<style>` with `@import` and tracking-pixel `<img>` still fire in sandboxed iframes.

- [ ] **Step 1: Write failing tests**

Append to `backend/tests/routers/test_email_body.py`:

```python
from app.services.email_body import sanitize_body_html


def test_sanitize_removes_script_tags() -> None:
    html = "<p>hello</p><script>alert(1)</script>"
    result = sanitize_body_html(html)
    assert "<script" not in result
    assert "hello" in result


def test_sanitize_removes_style_tags() -> None:
    html = "<style>body { background: url(https://track.example.com) }</style><p>hi</p>"
    result = sanitize_body_html(html)
    assert "<style" not in result
    assert "hi" in result


def test_sanitize_removes_link_tags() -> None:
    html = '<link rel="stylesheet" href="https://evil.example.com/x.css"><p>hi</p>'
    result = sanitize_body_html(html)
    assert "<link" not in result


def test_sanitize_removes_meta_refresh() -> None:
    html = '<meta http-equiv="refresh" content="0; url=https://evil.example.com"><p>hi</p>'
    result = sanitize_body_html(html)
    assert "<meta" not in result


def test_sanitize_removes_base_tag() -> None:
    html = '<base href="https://evil.example.com"><p>hi</p>'
    result = sanitize_body_html(html)
    assert "<base" not in result


def test_sanitize_removes_inline_event_handlers() -> None:
    html = '<p onclick="evil()" onmouseover="steal()">click me</p>'
    result = sanitize_body_html(html)
    assert "onclick" not in result
    assert "onmouseover" not in result
    assert "click me" in result


def test_sanitize_removes_onerror_on_img() -> None:
    html = '<img src="x" onerror="alert(1)">'
    result = sanitize_body_html(html)
    assert "onerror" not in result
```

- [ ] **Step 2: Run tests — expect failures**

```bash
cd backend && python -m pytest tests/routers/test_email_body.py -k "sanitize" -v
```

Expected: most new tests `FAILED` — style, link, meta, base, event handlers are not removed.

- [ ] **Step 3: Replace `sanitize_body_html` in `backend/app/services/email_body.py`**

Replace the existing function:

```python
_EVENT_HANDLER_RE = re.compile(r"^on\w+$", re.IGNORECASE)

_BLOCKED_TAGS = {"script", "style", "link", "meta", "base", "noscript"}


def sanitize_body_html(body_html: str) -> str:
    """Remove dangerous tags and all inline event handlers from email HTML.

    Blocked tags: script, style, link, meta, base, noscript.
    All on* attributes (onclick, onerror, onload, …) are stripped from
    every remaining tag.  The iframe in the detail panel already uses
    sandbox="" (no script execution), but this defence-in-depth layer
    also removes CSS tracking vectors and attribute-based JS injection.
    """
    soup = BeautifulSoup(body_html, "html.parser")

    # Remove blocked tags entirely (including their content for script/style)
    for tag_name in _BLOCKED_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Strip all on* event-handler attributes from every remaining tag
    for tag in soup.find_all(True):
        attrs_to_remove = [
            attr for attr in list(tag.attrs)
            if _EVENT_HANDLER_RE.match(attr)
        ]
        for attr in attrs_to_remove:
            del tag[attr]

    return str(soup)
```

Add `import re` at the top of the file if not already present (it is not — add it after the existing imports).

- [ ] **Step 4: Run tests — expect pass**

```bash
cd backend && python -m pytest tests/routers/test_email_body.py -v
```

All should pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/email_body.py backend/tests/routers/test_email_body.py
git commit -m "fix(security): strip style/link/meta/base and on* handlers in sanitize_body_html (#audit)"
```

---

## Task 5: TTL Eviction for In-Process Caches (JOBS, Rate-Limit, Refresh Locks)

**Files:**
- Modify: `backend/app/services/retriage.py`
- Modify: `backend/app/services/contact_tags.py`
- Modify: `backend/app/services/gmail_oauth.py`
- Test: `backend/tests/services/test_retriage.py` (extend)

**Context:** Three dicts grow without bound: `JOBS` in retriage and contact_tags (completed job records), `_last_request_at` in retriage (rate-limit timestamps), and `_refresh_locks` in gmail_oauth (one Lock per account). A helper that evicts entries older than a TTL is needed.

- [ ] **Step 1: Write failing test**

Append to `backend/tests/services/test_retriage.py`:

```python
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.services.retriage import JOBS, _last_request_at, _evict_stale_entries


def test_evict_stale_entries_removes_old_jobs() -> None:
    """Jobs older than ttl_seconds must be removed by evict_stale_entries."""
    job_id = "old_job"
    user_id = uuid4()
    # Simulate a completed job created 2 hours ago
    from app.services.retriage import RetriageJob
    old_job = RetriageJob(job_id=job_id, user_id=user_id, total=5)
    old_job.status = "done"
    JOBS[job_id] = old_job

    old_time = datetime.now(timezone.utc) - timedelta(seconds=7201)
    _last_request_at[user_id] = old_time

    _evict_stale_entries(ttl_seconds=3600)

    assert job_id not in JOBS
    assert user_id not in _last_request_at


def test_evict_stale_entries_keeps_recent_jobs() -> None:
    """Jobs younger than ttl_seconds must not be removed."""
    job_id = "new_job"
    user_id = uuid4()
    from app.services.retriage import RetriageJob
    new_job = RetriageJob(job_id=job_id, user_id=user_id, total=3)
    JOBS[job_id] = new_job
    _last_request_at[user_id] = datetime.now(timezone.utc)

    _evict_stale_entries(ttl_seconds=3600)

    assert job_id in JOBS
    assert user_id in _last_request_at
```

- [ ] **Step 2: Run test — expect failure**

```bash
cd backend && python -m pytest tests/services/test_retriage.py::test_evict_stale_entries_removes_old_jobs -v
```

Expected: `FAILED` — `ImportError: cannot import name '_evict_stale_entries'`

- [ ] **Step 3: Add `_evict_stale_entries` and `_created_at` tracking to `backend/app/services/retriage.py`**

Add a `created_at` field to `RetriageJob` and a cleanup function. Replace the dataclass and add the helper:

```python
@dataclass
class RetriageJob:
    job_id: str
    user_id: UUID
    total: int
    processed: int = 0
    status: Literal["running", "done", "failed"] = "running"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

Add `from dataclasses import dataclass, field` (replace existing `from dataclasses import dataclass`).

Then add the eviction helper after the JOBS dict:

```python
_JOB_TTL_SECONDS = 3600  # 1 hour


def _evict_stale_entries(ttl_seconds: int = _JOB_TTL_SECONDS) -> None:
    """Remove completed/failed jobs and stale rate-limit timestamps older than ttl_seconds."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
    stale_jobs = [
        jid for jid, job in list(JOBS.items())
        if job.status in ("done", "failed") and job.created_at < cutoff
    ]
    for jid in stale_jobs:
        JOBS.pop(jid, None)

    stale_users = [uid for uid, ts in list(_last_request_at.items()) if ts < cutoff]
    for uid in stale_users:
        _last_request_at.pop(uid, None)
```

Call it at the top of `start_retriage` (before checking rate limit) so every call self-cleans:

```python
async def start_retriage(user_id: UUID, context: str) -> RetriageJob:
    _evict_stale_entries()          # ← add this line
    now = datetime.now(timezone.utc)
    # ... rest unchanged
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd backend && python -m pytest tests/services/test_retriage.py -v
```

- [ ] **Step 5: Apply the same pattern to `backend/app/services/contact_tags.py`**

Add `created_at` to `ContactTagJob`:

```python
from dataclasses import dataclass, field   # update import

@dataclass
class ContactTagJob:
    job_id: str
    user_id: UUID
    total: int
    processed: int = 0
    status: Literal["running", "done", "failed"] = "running"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

Add `from datetime import datetime, timezone` if not already present.

Add eviction helper:

```python
_JOB_TTL_SECONDS = 3600


def _evict_stale_contact_jobs() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=_JOB_TTL_SECONDS)
    stale = [
        jid for jid, job in list(JOBS.items())
        if job.status in ("done", "failed") and job.created_at < cutoff
    ]
    for jid in stale:
        JOBS.pop(jid, None)
```

Add `from datetime import datetime, timedelta, timezone` at top (merge with existing datetime imports).

Call it at the start of `apply_retroactive_async`:

```python
async def apply_retroactive_async(tag_id: UUID, user_id: UUID, identifier: str) -> str:
    _evict_stale_contact_jobs()    # ← add this line
    job_id = uuid.uuid4().hex
    # ... rest unchanged
```

- [ ] **Step 6: Fix `_refresh_locks` leak in `backend/app/services/gmail_oauth.py`**

The fix here is simply to not accumulate locks for disconnected accounts. Change `refresh_tokens` to clean up the lock after use:

```python
async def refresh_tokens(account_id: UUID, refresh_token: str) -> OAuthTokens:
    if account_id not in _refresh_locks:
        _refresh_locks[account_id] = asyncio.Lock()
    async with _refresh_locks[account_id]:
        account = await get_account(account_id)
        if account.oauth_token.expires_at > datetime.now(timezone.utc) + timedelta(seconds=60):
            return account.oauth_token

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.gmail_client_id,
                    "client_secret": settings.gmail_client_secret,
                },
            )

        if resp.status_code != 200:
            body = resp.json()
            is_invalid = body.get("error") == "invalid_grant"
            if is_invalid:
                # Account is permanently revoked — drop the lock entry
                _refresh_locks.pop(account_id, None)
            raise RefreshFailed(is_invalid_grant=is_invalid)

        data = resp.json()
        try:
            new_tokens = OAuthTokens(
                access_token=data["access_token"],
                refresh_token=refresh_token,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"]),
                scope=data.get("scope", ""),
            )
        except (KeyError, TypeError) as exc:
            raise RefreshFailed(is_invalid_grant=False) from exc
        await update_oauth_token(account_id, new_tokens)
        return new_tokens
```

- [ ] **Step 7: Run all service tests**

```bash
cd backend && python -m pytest tests/services/ -v
```

All should pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/retriage.py \
        backend/app/services/contact_tags.py \
        backend/app/services/gmail_oauth.py \
        backend/tests/services/test_retriage.py
git commit -m "fix(memory): TTL eviction for JOBS, rate-limit timestamps, and refresh locks (#audit)"
```

---

## Task 6: Enforce `BATCH_COST_CAP_USD` in the AI Worker

**Files:**
- Modify: `backend/app/services/openai_client.py`
- Modify: `backend/app/tasks/ai_worker.py`
- Test: `backend/tests/tasks/test_ai_worker.py` (extend)

**Context:** `BATCH_COST_CAP_USD = 0.50` is defined in `ai_worker.py` but never checked. `call_json` already tracks cost via `_record_usage` and returns the usage token counts. We need `call_json` to also return the cost so the worker can accumulate it and stop the batch if the cap is hit.

- [ ] **Step 1: Write failing test**

Append to `backend/tests/tasks/test_ai_worker.py`:

```python
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.tasks.ai_worker import process_batch, BATCH_COST_CAP_USD


@pytest.mark.asyncio
async def test_process_batch_stops_when_cost_cap_exceeded() -> None:
    """process_batch must stop processing once accumulated cost exceeds BATCH_COST_CAP_USD."""
    from app.models.email import Email
    from datetime import datetime, timezone

    def _make_email():
        return Email(
            id=uuid4(),
            user_id=uuid4(),
            account_id=uuid4(),
            gmail_id="msg1",
            subject="test",
            sender="a@b.com",
            is_read=False,
            labels=[],
            is_archived=False,
            ai_processed=False,
            created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )

    # 5 emails in the batch
    emails = [_make_email() for _ in range(5)]
    processed_ids = []

    async def _fake_triage(email, _ctx):
        from app.services.triage import TriageResult
        return TriageResult(
            category="auto_archive",
            summary="test",
            triage_context="Daily",
            _cost_usd=Decimal("0.30"),  # each call costs $0.30 → cap hit after 2nd
        )

    from app.models.user import User
    from datetime import datetime, timezone as tz
    fake_user = User(
        id=emails[0].user_id,
        email="u@x.com",
        default_context="Daily",
        created_at=datetime(2025, 1, 1, tzinfo=tz.utc),
    )

    with (
        patch("app.tasks.ai_worker.list_unprocessed_emails", new=AsyncMock(return_value=emails)),
        patch("app.tasks.ai_worker.get_user", new=AsyncMock(return_value=fake_user)),
        patch("app.tasks.ai_worker.triage_email", side_effect=_fake_triage),
        patch("app.tasks.ai_worker.apply_triage_result", new=AsyncMock()),
    ):
        count = await process_batch()

    # With a $0.50 cap and $0.30/email, batch should stop after 2 emails (cost = $0.60 > $0.50)
    assert count <= 2, f"Expected ≤2 processed before cap, got {count}"
```

**Note:** This test drives out the API contract — `triage_email` must return a result that includes `_cost_usd`. We implement that in the next step.

- [ ] **Step 2: Run test — expect failure**

```bash
cd backend && python -m pytest tests/tasks/test_ai_worker.py::test_process_batch_stops_when_cost_cap_exceeded -v
```

Expected: `FAILED` — `TriageResult` has no `_cost_usd` attribute.

- [ ] **Step 3: Add `cost_usd` to `TriageResult` in `backend/app/services/triage.py`**

```python
@dataclass
class TriageResult:
    category: str
    summary: str
    triage_context: str
    deadline_extracted: date | None = None
    action_items: list[str] | None = None
    is_pickup_code: bool = False
    pickup_code: str | None = None
    pickup_expiry: date | None = None
    retailer: str | None = None
    locker_location: str | None = None
    cost_usd: Decimal = field(default_factory=Decimal)  # ← add this field
```

Add `from decimal import Decimal` and `from dataclasses import dataclass, field` (update existing imports).

- [ ] **Step 4: Make `call_json` return cost alongside the parsed response**

In `backend/app/services/openai_client.py`, change `call_json` to also return the cost. Because this would break all callers, the cleanest approach is to add a new wrapper `call_json_with_cost`:

```python
async def call_json_with_cost(
    *,
    system: str,
    user: str,
    response_model: type[T],
    kind: str,
    user_id: UUID,
    email_id: UUID | None = None,
) -> tuple[T, Decimal]:
    """Like call_json but also returns the USD cost of this call."""
    raw, prompt_tokens, completion_tokens = await _completion(system, user)
    cost = _usage_cost(prompt_tokens, completion_tokens)
    await _record_usage(
        user_id=user_id,
        email_id=email_id,
        kind=kind,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raw, pt2, ct2 = await _completion(system, user)
        cost += _usage_cost(pt2, ct2)
        await _record_usage(
            user_id=user_id,
            email_id=email_id,
            kind=kind,
            prompt_tokens=pt2,
            completion_tokens=ct2,
        )
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.warning("invalid json from openai kind=%s raw=%s", kind, raw)
            raise AIInvalidResponse(str(exc)) from exc

    try:
        parsed = response_model.model_validate(data)
    except ValidationError as exc:
        logger.warning("invalid openai response kind=%s raw=%s err=%s", kind, raw, exc)
        raise AIInvalidResponse(str(exc)) from exc

    return parsed, cost
```

- [ ] **Step 5: Update `triage_email` in `backend/app/services/triage.py` to use `call_json_with_cost` and accumulate cost**

Change the import at the top:

```python
from app.services.openai_client import call_json, call_json_with_cost
```

Update the main triage call and accumulate cost in the result:

```python
async def triage_email(email: Email, user_context: str) -> TriageResult:
    body = _email_body(email)
    if not body.strip():
        return TriageResult(
            category="auto_archive",
            summary="Image-only email — no readable text.",
            triage_context=user_context,
        )

    user_msg = (
        f"From: {_email_sender(email)}\n"
        f"Subject: {email.subject or ''}\n"
        f"Body: {body[:4000]}"
    )
    triage, triage_cost = await call_json_with_cost(
        system=TRIAGE_PROMPTS[user_context],
        user=user_msg,
        response_model=TriageResponse,
        kind="triage",
        user_id=email.user_id,
        email_id=email.id,
    )

    result = TriageResult(
        category=triage.category,
        summary=triage.summary,
        triage_context=user_context,
        cost_usd=triage_cost,
    )

    tasks = []
    if triage.has_deadline:
        received_at = email.received_at.isoformat() if email.received_at else ""
        tasks.append(
            (
                "deadline",
                call_json_with_cost(
                    system=DEADLINE_PROMPT,
                    user=f"received_at: {received_at}\n\n{body}",
                    response_model=DeadlineResponse,
                    kind="deadline",
                    user_id=email.user_id,
                    email_id=email.id,
                ),
            )
        )
    if triage.has_action_items:
        tasks.append(
            (
                "actions",
                call_json_with_cost(
                    system=ACTION_ITEMS_PROMPT,
                    user=body,
                    response_model=ActionItemsResponse,
                    kind="action_items",
                    user_id=email.user_id,
                    email_id=email.id,
                ),
            )
        )
    if triage.is_pickup_code or pickup_code_prefilter(email):
        tasks.append(
            (
                "pickup",
                call_json_with_cost(
                    system=PICKUP_CODE_PROMPT,
                    user=f"Subject: {email.subject or ''}\nBody: {body}",
                    response_model=PickupCodeResponse,
                    kind="pickup",
                    user_id=email.user_id,
                    email_id=email.id,
                ),
            )
        )

    if tasks:
        outcomes = await asyncio.gather(*(task for _, task in tasks), return_exceptions=True)
        for (kind, _), outcome in zip(tasks, outcomes):
            if isinstance(outcome, Exception):
                logger.warning("extraction failed kind=%s err=%s", kind, outcome)
                continue
            parsed, step_cost = outcome
            result.cost_usd += step_cost
            if kind == "deadline":
                result.deadline_extracted = parsed.deadline
            elif kind == "actions":
                result.action_items = parsed.action_items
            elif kind == "pickup" and parsed.pickup_code:
                result.is_pickup_code = True
                result.pickup_code = parsed.pickup_code
                result.pickup_expiry = parsed.pickup_expiry
                result.retailer = parsed.retailer
                result.locker_location = parsed.locker_location

    return result
```

- [ ] **Step 6: Update `process_batch` in `backend/app/tasks/ai_worker.py` to enforce cost cap**

Replace the existing `process_batch` function:

```python
async def process_batch() -> int:
    emails = await list_unprocessed_emails(limit=BATCH_SIZE)
    if not emails:
        return 0

    user_ids = list({email.user_id for email in emails})
    contexts = await asyncio.gather(*(get_user(uid) for uid in user_ids))
    ctx_by_user = {user.id: user.default_context for user in contexts}

    processed = 0
    batch_cost = Decimal("0")

    for email in emails:
        if batch_cost >= Decimal(str(BATCH_COST_CAP_USD)):
            logger.warning(
                "ai_worker cost cap $%.2f reached after %d emails — stopping batch",
                BATCH_COST_CAP_USD,
                processed,
            )
            break
        try:
            result = await triage_email(email, ctx_by_user[email.user_id])
            await apply_triage_result(email.id, result)
            batch_cost += result.cost_usd
            processed += 1
        except (AIInvalidResponse, AIServiceUnavailable) as exc:
            logger.warning("ai failed email_id=%s err=%s", email.id, exc)
            await mark_ai_failed(email.id)

    return processed
```

Add `from decimal import Decimal` at the top of `ai_worker.py`.

- [ ] **Step 7: Run test — expect pass**

```bash
cd backend && python -m pytest tests/tasks/test_ai_worker.py -v
```

- [ ] **Step 8: Run all service + task tests**

```bash
cd backend && python -m pytest tests/services/test_triage.py tests/tasks/ -v
```

All should pass.

- [ ] **Step 9: Commit**

```bash
git add backend/app/services/triage.py \
        backend/app/services/openai_client.py \
        backend/app/tasks/ai_worker.py \
        backend/tests/tasks/test_ai_worker.py
git commit -m "feat(ai): enforce BATCH_COST_CAP_USD per batch, propagate cost through TriageResult (#audit)"
```

---

## Task 7: Force `action_required` for Tagged-Contact Emails

**Files:**
- Modify: `backend/app/tasks/ai_worker.py`
- Modify: `backend/app/db/emails.py`
- Test: `backend/tests/services/test_triage.py` (extend)

**Context:** The spec says "emails from tagged contacts always highlighted regardless of context." Visual highlighting via `contact_tag` is already implemented, but the triage category itself can still be `auto_archive`, hiding the email in counts and the "All" tab collapse. The fix: after `apply_triage_result`, if `email.contact_tag_id` is set and the category is `auto_archive`, upgrade it to `worth_reading`.

- [ ] **Step 1: Write failing test**

Append to `backend/tests/services/test_triage.py`:

```python
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import pytest


@pytest.mark.asyncio
async def test_tagged_contact_email_upgraded_from_auto_archive() -> None:
    """apply_triage_result_with_tag_override must upgrade auto_archive to worth_reading
    when the email has a contact_tag_id set."""
    from app.tasks.ai_worker import _apply_with_tag_override
    from app.services.triage import TriageResult
    from decimal import Decimal

    email_id = uuid4()
    result = TriageResult(
        category="auto_archive",
        summary="Newsletter",
        triage_context="Daily",
    )
    override_called_with = {}

    async def _fake_apply(eid, res):
        override_called_with["category"] = res.category

    with patch("app.tasks.ai_worker.apply_triage_result", side_effect=_fake_apply):
        await _apply_with_tag_override(email_id, result, has_contact_tag=True)

    assert override_called_with["category"] == "worth_reading"


@pytest.mark.asyncio
async def test_tagged_contact_email_does_not_downgrade_action_required() -> None:
    """action_required emails must not be changed even if tagged."""
    from app.tasks.ai_worker import _apply_with_tag_override
    from app.services.triage import TriageResult

    email_id = uuid4()
    result = TriageResult(
        category="action_required",
        summary="Interview invite",
        triage_context="Job Hunting",
    )
    override_called_with = {}

    async def _fake_apply(eid, res):
        override_called_with["category"] = res.category

    with patch("app.tasks.ai_worker.apply_triage_result", side_effect=_fake_apply):
        await _apply_with_tag_override(email_id, result, has_contact_tag=True)

    assert override_called_with["category"] == "action_required"


@pytest.mark.asyncio
async def test_untagged_email_auto_archive_not_changed() -> None:
    """Without a contact tag, auto_archive must stay auto_archive."""
    from app.tasks.ai_worker import _apply_with_tag_override
    from app.services.triage import TriageResult

    email_id = uuid4()
    result = TriageResult(
        category="auto_archive",
        summary="Newsletter",
        triage_context="Daily",
    )
    override_called_with = {}

    async def _fake_apply(eid, res):
        override_called_with["category"] = res.category

    with patch("app.tasks.ai_worker.apply_triage_result", side_effect=_fake_apply):
        await _apply_with_tag_override(email_id, result, has_contact_tag=False)

    assert override_called_with["category"] == "auto_archive"
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd backend && python -m pytest tests/services/test_triage.py -k "tagged_contact" -v
```

Expected: `FAILED` — `ImportError: cannot import name '_apply_with_tag_override'`

- [ ] **Step 3: Add `_apply_with_tag_override` to `backend/app/tasks/ai_worker.py`**

Add after the imports:

```python
async def _apply_with_tag_override(
    email_id: UUID,
    result: TriageResult,
    has_contact_tag: bool,
) -> None:
    """Write triage result, upgrading auto_archive → worth_reading for tagged contacts."""
    if has_contact_tag and result.category == "auto_archive":
        result = TriageResult(
            category="worth_reading",
            summary=result.summary,
            triage_context=result.triage_context,
            deadline_extracted=result.deadline_extracted,
            action_items=result.action_items,
            is_pickup_code=result.is_pickup_code,
            pickup_code=result.pickup_code,
            pickup_expiry=result.pickup_expiry,
            retailer=result.retailer,
            locker_location=result.locker_location,
            cost_usd=result.cost_usd,
        )
    await apply_triage_result(email_id, result)
```

Add `from uuid import UUID` if not already imported.

Then update `process_batch` to use it, passing `has_contact_tag`:

```python
        try:
            result = await triage_email(email, ctx_by_user[email.user_id])
            has_tag = email.contact_tag is not None   # ← check embedded contact tag
            await _apply_with_tag_override(email.id, result, has_contact_tag=has_tag)
            batch_cost += result.cost_usd
            processed += 1
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd backend && python -m pytest tests/services/test_triage.py -k "tagged_contact" -v
```

- [ ] **Step 5: Run all service tests**

```bash
cd backend && python -m pytest tests/services/ tests/tasks/ -v
```

All should pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/tasks/ai_worker.py backend/tests/services/test_triage.py
git commit -m "feat(triage): upgrade auto_archive→worth_reading for tagged-contact emails (#audit)"
```

---

## Task 8: Store Sender Display Name

**Files:**
- Create: `backend/supabase/migrations/019_sender_name.sql`
- Modify: `backend/app/models/email.py`
- Modify: `backend/app/services/gmail_sync.py`
- Modify: `backend/app/db/emails.py`
- Modify: `backend/supabase/migrations/017_security_hardening.sql` → already renamed to `017_security_hardening.sql`; the `upsert_email_record` function must be updated in a new migration
- Modify: `frontend/types/index.ts`
- Modify: `frontend/components/inbox/email-card.tsx`
- Modify: `frontend/components/inbox/email-detail-panel.tsx`

**Context:** Gmail `From:` headers look like `"Amazon <noreply@amazon.com>"`. Currently only `noreply@amazon.com` is stored. We need to also store `"Amazon"` in a new `sender_name` column and show it in the UI instead of the raw email address.

- [ ] **Step 1: Create migration `backend/supabase/migrations/019_sender_name.sql`**

```sql
-- 019_sender_name.sql
-- Add sender_name column to store the human-readable display name from the From: header.
ALTER TABLE public.emails
    ADD COLUMN IF NOT EXISTS sender_name TEXT;

-- Update upsert_email_record to accept and store sender_name.
CREATE OR REPLACE FUNCTION public.upsert_email_record(
    p_account_id  UUID,
    p_user_id     UUID,
    p_gmail_id    TEXT,
    p_subject     TEXT,
    p_sender      TEXT,
    p_sender_name TEXT,
    p_body_text   TEXT,
    p_received_at TIMESTAMPTZ
) RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    _is_insert BOOLEAN;
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM public.connected_accounts
        WHERE id = p_account_id
          AND user_id = p_user_id
          AND disconnected_at IS NULL
    ) THEN
        RAISE EXCEPTION 'account does not belong to user'
            USING ERRCODE = '42501';
    END IF;

    INSERT INTO public.emails
        (account_id, user_id, gmail_id, subject, sender, sender_name, body_text, received_at)
    VALUES
        (p_account_id, p_user_id, p_gmail_id, p_subject, p_sender, p_sender_name, p_body_text, p_received_at)
    ON CONFLICT (account_id, gmail_id) DO UPDATE SET
        subject     = EXCLUDED.subject,
        body_text   = EXCLUDED.body_text,
        sender      = EXCLUDED.sender,
        sender_name = EXCLUDED.sender_name
    RETURNING (xmax = 0) INTO _is_insert;

    RETURN CASE WHEN _is_insert THEN 'inserted' ELSE 'updated' END;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.upsert_email_record(
    UUID, UUID, TEXT, TEXT, TEXT, TEXT, TEXT, TIMESTAMPTZ
) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.upsert_email_record(
    UUID, UUID, TEXT, TEXT, TEXT, TEXT, TEXT, TIMESTAMPTZ
) TO service_role;
```

- [ ] **Step 2: Add `sender_name` to `ParsedEmail` and `Email` in `backend/app/models/email.py`**

In `ParsedEmail`:

```python
class ParsedEmail(BaseModel):
    external_id: str
    sender_email: str
    sender_name: str | None = None   # ← add this
    subject: str
    body_preview: str
    received_at: datetime
```

In `Email`:

```python
class Email(BaseModel):
    # ... existing fields ...
    sender: str | None = None
    sender_name: str | None = None   # ← add this line after sender
```

- [ ] **Step 3: Parse sender display name in `backend/app/services/gmail_sync.py`**

Replace the sender extraction block in `fetch_message`:

```python
_SENDER_RE = re.compile(r"<([^>]+)>")
_DISPLAY_NAME_RE = re.compile(r'^"?([^"<]+?)"?\s*<')


async def fetch_message(service, message_id: str) -> ParsedEmail | None:
    # ... existing code up to header extraction ...

    from_header = headers.get("From", "")
    m = _SENDER_RE.search(from_header)
    sender_email = (m.group(1) if m else from_header).lower().strip()

    # Extract display name: e.g. "Amazon" from "Amazon <noreply@amazon.com>"
    name_match = _DISPLAY_NAME_RE.match(from_header)
    sender_name = name_match.group(1).strip() if name_match else None
    # Fall back to local-part of email if no display name found
    if not sender_name:
        sender_name = sender_email.split("@")[0] if "@" in sender_email else None

    # ... rest of existing code ...

    return ParsedEmail(
        external_id=message_id,
        sender_email=sender_email,
        sender_name=sender_name,    # ← add
        subject=subject,
        body_preview=body_preview,
        received_at=received_at,
    )
```

- [ ] **Step 4: Pass `sender_name` through `upsert_email` in `backend/app/db/emails.py`**

Update `upsert_email`:

```python
async def upsert_email(
    account_id: UUID,
    user_id: UUID,
    parsed: ParsedEmail,
) -> Literal["inserted", "updated"]:
    def _do() -> str:
        result = get_service_client().rpc(
            "upsert_email_record",
            {
                "p_account_id": str(account_id),
                "p_user_id": str(user_id),
                "p_gmail_id": parsed.external_id,
                "p_subject": parsed.subject,
                "p_sender": parsed.sender_email,
                "p_sender_name": parsed.sender_name,   # ← add
                "p_body_text": parsed.body_preview,
                "p_received_at": parsed.received_at.isoformat(),
            },
        ).execute()
        return result.data

    return await asyncio.to_thread(_do)
```

- [ ] **Step 5: Add `sender_name` to frontend types in `frontend/types/index.ts`**

```typescript
export type Email = {
  // ... existing fields ...
  sender: string | null;
  sender_name: string | null;   // ← add after sender
```

- [ ] **Step 6: Show `sender_name` in email card (`frontend/components/inbox/email-card.tsx`)**

Replace the sender display line:

```tsx
<span className="truncate font-semibold">
  {email.sender_name ?? email.sender ?? "(unknown)"}
</span>
```

- [ ] **Step 7: Show `sender_name` in email detail panel (`frontend/components/inbox/email-detail-panel.tsx`)**

Update the sender line:

```tsx
<div className="text-sm text-muted-foreground">
  {email.sender_name
    ? `${email.sender_name} <${email.sender ?? ""}>`
    : email.sender ?? "(unknown sender)"}
  {email.received_at ? ` • ${format(new Date(email.received_at), "PPp")}` : ""}
</div>
```

- [ ] **Step 8: Write a test for the display name parser**

Append to `backend/tests/services/test_gmail_sync.py` (create if missing):

```python
from app.services.gmail_sync import fetch_message
import pytest


def test_parse_display_name_from_from_header():
    """_DISPLAY_NAME_RE must extract display name from typical From: headers."""
    from app.services.gmail_sync import _DISPLAY_NAME_RE, _SENDER_RE

    from_header = 'Amazon <noreply@amazon.com>'
    m = _SENDER_RE.search(from_header)
    assert m and m.group(1) == "noreply@amazon.com"
    n = _DISPLAY_NAME_RE.match(from_header)
    assert n and n.group(1).strip() == "Amazon"


def test_parse_quoted_display_name():
    from app.services.gmail_sync import _DISPLAY_NAME_RE
    from_header = '"John Doe" <john@example.com>'
    n = _DISPLAY_NAME_RE.match(from_header)
    assert n and n.group(1).strip() == "John Doe"


def test_no_display_name_returns_none_for_name():
    from app.services.gmail_sync import _DISPLAY_NAME_RE
    from_header = 'noreply@amazon.com'
    n = _DISPLAY_NAME_RE.match(from_header)
    assert n is None
```

- [ ] **Step 9: Run backend tests**

```bash
cd backend && python -m pytest tests/services/test_gmail_sync.py -v
```

All should pass.

- [ ] **Step 10: Commit**

```bash
git add backend/supabase/migrations/019_sender_name.sql \
        backend/app/models/email.py \
        backend/app/services/gmail_sync.py \
        backend/app/db/emails.py \
        frontend/types/index.ts \
        frontend/components/inbox/email-card.tsx \
        frontend/components/inbox/email-detail-panel.tsx \
        backend/tests/services/test_gmail_sync.py
git commit -m "feat(inbox): store and display sender display name from From: header (#audit)"
```

---

## Task 9: Implement Data Retention Enforcement

**Files:**
- Create: `backend/supabase/migrations/020_data_retention.sql`
- Modify: `backend/app/tasks/scheduler.py`
- Test: `backend/tests/services/test_digest.py` (extend with retention test in a new file)

**Context:** `data_retention_days` is stored on `users` but never enforced. Emails older than `data_retention_days` must be deleted by a nightly cron job.

- [ ] **Step 1: Create the SQL helper function**

Create `backend/supabase/migrations/020_data_retention.sql`:

```sql
-- 020_data_retention.sql
-- Adds a stored procedure that deletes emails older than each user's retention window.
-- Called nightly by the backend scheduler.

CREATE OR REPLACE FUNCTION public.apply_data_retention()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    deleted_count INTEGER := 0;
    _count INTEGER;
BEGIN
    -- Delete emails older than data_retention_days for each user who set a limit.
    -- Users with data_retention_days IS NULL are exempt (keep forever).
    WITH to_delete AS (
        SELECT e.id
        FROM public.emails e
        JOIN public.users u ON u.id = e.user_id
        WHERE u.data_retention_days IS NOT NULL
          AND e.received_at < now() - (u.data_retention_days * INTERVAL '1 day')
    )
    DELETE FROM public.emails
    WHERE id IN (SELECT id FROM to_delete);

    GET DIAGNOSTICS _count = ROW_COUNT;
    deleted_count := _count;
    RETURN deleted_count;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.apply_data_retention() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.apply_data_retention() TO service_role;
```

- [ ] **Step 2: Write a test for the scheduler job**

Create `backend/tests/tasks/test_scheduler.py`:

```python
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_enforce_data_retention_calls_rpc() -> None:
    """enforce_data_retention must call the apply_data_retention RPC and log the count."""
    rpc_calls = []

    class _RpcResult:
        data = 3  # 3 rows deleted

    class _Chain:
        def rpc(self, name, *_args, **_kwargs):
            rpc_calls.append(name)
            return self

        def execute(self):
            return _RpcResult()

    with patch("app.tasks.scheduler.get_service_client", return_value=_Chain()):
        from app.tasks.scheduler import enforce_data_retention
        await enforce_data_retention()

    assert "apply_data_retention" in rpc_calls
```

- [ ] **Step 3: Run test — expect failure**

```bash
cd backend && python -m pytest tests/tasks/test_scheduler.py::test_enforce_data_retention_calls_rpc -v
```

Expected: `FAILED` — `ImportError: cannot import name 'enforce_data_retention'`

- [ ] **Step 4: Add `enforce_data_retention` job to `backend/app/tasks/scheduler.py`**

```python
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.connected_accounts import list_accounts_due_for_sync
from app.db.supabase import get_service_client
from app.services.gmail_sync import sync_account

logger = logging.getLogger(__name__)

_GLOBAL_SYNC_CONCURRENCY = 10


async def sync_all_due_accounts() -> None:
    import time
    start = time.monotonic()
    logger.info("scheduler job_start sync_all_due_accounts")

    accounts = await list_accounts_due_for_sync()
    semaphore = asyncio.Semaphore(_GLOBAL_SYNC_CONCURRENCY)

    async def _sync_one(account_id):
        async with semaphore:
            try:
                return await sync_account(account_id)
            except Exception as exc:
                logger.error("Scheduler sync error for account %s: %s", account_id, exc)
                return None

    results = await asyncio.gather(*[_sync_one(a.id) for a in accounts])

    total_synced = sum(1 for r in results if r is not None)
    total_errors = sum(1 for r in results if r is None)
    elapsed = time.monotonic() - start
    logger.info(
        "scheduler job_end sync_all_due_accounts total_synced=%d total_errors=%d elapsed_s=%.2f",
        total_synced,
        total_errors,
        elapsed,
    )


async def enforce_data_retention() -> None:
    """Delete emails older than each user's data_retention_days setting."""
    logger.info("scheduler job_start enforce_data_retention")

    def _run():
        result = get_service_client().rpc("apply_data_retention").execute()
        return result.data  # integer count of deleted rows

    deleted = await asyncio.to_thread(_run)
    logger.info("scheduler job_end enforce_data_retention deleted=%s", deleted)


def make_scheduler() -> AsyncIOScheduler:
    sched = AsyncIOScheduler()
    sched.add_job(
        sync_all_due_accounts,
        "interval",
        minutes=5,
        id="sync_all_due_accounts",
    )
    sched.add_job(
        enforce_data_retention,
        "cron",
        hour=3,           # 3 AM UTC nightly
        minute=0,
        id="enforce_data_retention",
    )
    return sched
```

- [ ] **Step 5: Run test — expect pass**

```bash
cd backend && python -m pytest tests/tasks/test_scheduler.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/supabase/migrations/020_data_retention.sql \
        backend/app/tasks/scheduler.py \
        backend/tests/tasks/test_scheduler.py
git commit -m "feat(privacy): enforce data_retention_days with nightly scheduler job (#audit)"
```

---

## Task 10: Add Edit Contact Tag (PATCH /contacts/{id})

**Files:**
- Modify: `backend/app/models/contact_tag.py`
- Modify: `backend/app/db/contact_tags.py`
- Modify: `backend/app/routers/contacts.py`
- Test: `backend/tests/routers/test_contacts.py` (extend)

**Context:** Users can only add/delete tags. There is no way to update a tag's `custom_label` or `color` after creation.

- [ ] **Step 1: Write failing test**

Append to `backend/tests/routers/test_contacts.py`:

```python
def test_patch_contact_updates_label_and_color(authed_client: TestClient) -> None:
    from datetime import datetime, timezone
    from uuid import uuid4
    from app.models.contact_tag import ContactTag

    tag = ContactTag(
        id=uuid4(),
        user_id=_USER_ID,
        identifier="prof@uw.edu",
        tag="professor",
        custom_label="My Prof",
        color="#FF0000",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    with patch("app.routers.contacts.update_tag", new=AsyncMock(return_value=tag)):
        resp = authed_client.patch(
            f"/contacts/{tag.id}",
            json={"custom_label": "My Prof", "color": "#FF0000"},
        )
    assert resp.status_code == 200
    assert resp.json()["custom_label"] == "My Prof"
    assert resp.json()["color"] == "#FF0000"


def test_patch_contact_not_found(authed_client: TestClient) -> None:
    from uuid import uuid4
    with patch("app.routers.contacts.update_tag", new=AsyncMock(return_value=None)):
        resp = authed_client.patch(
            f"/contacts/{uuid4()}",
            json={"custom_label": "X"},
        )
    assert resp.status_code == 404
```

Make sure `_USER_ID` is defined at module level and `authed_client` fixture exists in this test file (it already does from the existing tests).

- [ ] **Step 2: Run tests — expect failure**

```bash
cd backend && python -m pytest tests/routers/test_contacts.py::test_patch_contact_updates_label_and_color -v
```

Expected: `FAILED` — router has no PATCH route.

- [ ] **Step 3: Add `ContactTagUpdate` to `backend/app/models/contact_tag.py`**

Append to the existing file:

```python
class ContactTagUpdate(BaseModel):
    custom_label: str | None = None
    color: str | None = None
```

- [ ] **Step 4: Add `update_tag` to `backend/app/db/contact_tags.py`**

Append:

```python
async def update_tag(tag_id: UUID, user_id: UUID, changes: dict[str, Any]) -> ContactTag | None:
    def _update() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("contact_tags")
            .update(changes)
            .eq("id", str(tag_id))
            .eq("user_id", str(user_id))
            .select("*")
            .maybe_single()
            .execute()
        )
        return result.data

    row = await asyncio.to_thread(_update)
    if not row:
        return None
    return ContactTag(**row)
```

Add `from typing import Any` if not already imported.

- [ ] **Step 5: Add PATCH route to `backend/app/routers/contacts.py`**

Add import:

```python
from app.models.contact_tag import ContactTag, ContactTagCreate, ContactTagUpdate, ContactJobStatus, ContactsGrouped, CreateContactResponse
from app.db.contact_tags import apply_retroactive_sync, count_emails_for_identifier, create_tag, delete_tag, get_tag, list_user_tags, update_tag
```

Add the route:

```python
@router.patch("/contacts/{tag_id}", response_model=ContactTag)
async def patch_contact(
    tag_id: UUID,
    body: ContactTagUpdate,
    claims: UserClaims = Depends(get_current_user),
) -> ContactTag:
    changes: dict[str, object] = {}
    if body.custom_label is not None:
        changes["custom_label"] = body.custom_label
    if body.color is not None:
        changes["color"] = body.color
    if not changes:
        raise HTTPException(status_code=422, detail="No updatable fields provided")
    updated = await update_tag(tag_id, claims.user_id, changes)
    if updated is None:
        raise HTTPException(status_code=404, detail="Contact tag not found")
    return updated
```

- [ ] **Step 6: Run tests — expect pass**

```bash
cd backend && python -m pytest tests/routers/test_contacts.py -v
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/contact_tag.py \
        backend/app/db/contact_tags.py \
        backend/app/routers/contacts.py \
        backend/tests/routers/test_contacts.py
git commit -m "feat(contacts): add PATCH /contacts/{id} to edit label and color (#audit)"
```

---

## Task 11: Fix `ContactTagBadge` to Use Next.js `<Link>`

**Files:**
- Modify: `frontend/components/inbox/contact-tag-badge.tsx`
- Test: `frontend/tests/inbox/EmailCard.test.tsx` (extend)

**Context:** The badge uses `<a href>` which causes a full browser navigation and wipes React Query cache. Must use Next.js `<Link>` for client-side routing.

- [ ] **Step 1: Write failing test**

Append to `frontend/tests/inbox/EmailCard.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { ContactTagBadge } from "@/components/inbox/contact-tag-badge";

describe("ContactTagBadge", () => {
  it("renders a Next.js Link (not an anchor) for client-side navigation", () => {
    render(
      <ContactTagBadge
        tag={{ label: "Recruiter", color: "#F59E0B" }}
        sender="recruiter@company.com"
      />
    );
    // Next.js Link renders an <a> but via the router — test the href attr
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute(
      "href",
      "/contacts?identifier=recruiter%40company.com",
    );
  });
});
```

- [ ] **Step 2: Run test**

```bash
cd frontend && npx vitest run tests/inbox/EmailCard.test.tsx --reporter=verbose
```

This will likely pass already (since `<a href>` also renders with `role="link"`). The meaningful behaviour change is the client-side routing — we validate this exists via the component change below.

- [ ] **Step 3: Replace `<a>` with `<Link>` in `frontend/components/inbox/contact-tag-badge.tsx`**

```tsx
import Link from "next/link";

export function ContactTagBadge({
  tag,
  sender,
}: {
  tag: { label: string; color: string } | null | undefined;
  sender?: string | null;
}) {
  if (!tag) return null;
  const href = sender
    ? `/contacts?identifier=${encodeURIComponent(sender)}`
    : "/contacts";
  return (
    <Link
      href={href}
      onClick={(event) => event.stopPropagation()}
      className="inline-flex shrink-0 items-center rounded-md px-2 py-0.5 text-xs font-medium text-slate-900 transition hover:ring-1 hover:ring-slate-400"
      style={{ backgroundColor: tag.color }}
      aria-label={`Manage contact tag for ${sender ?? tag.label}`}
    >
      {tag.label}
    </Link>
  );
}
```

- [ ] **Step 4: Run all inbox tests**

```bash
cd frontend && npx vitest run tests/inbox/ --reporter=verbose
```

All should pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/components/inbox/contact-tag-badge.tsx \
        frontend/tests/inbox/EmailCard.test.tsx
git commit -m "fix(inbox): ContactTagBadge uses Next.js Link for client-side routing (#audit)"
```

---

## Task 12: Add Active Nav Link Styling

**Files:**
- Modify: `frontend/app/layout.tsx`

**Context:** The nav renders all five links identically regardless of the current route. `usePathname()` must drive an active-state style.

- [ ] **Step 1: Update `frontend/app/layout.tsx`**

The layout is a Server Component. To use `usePathname()` (a Client hook), extract the nav into a `"use client"` component. Create an inline client component at the top of the file:

```tsx
import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Inter } from "next/font/google";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { SignOutButton } from "@/components/sign-out-button";
import { Providers } from "@/components/providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "InboxIQ",
  description: "AI-powered unified email — connect Gmail and triage your inbox",
};

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/inbox", label: "Inbox" },
  { href: "/packages", label: "Packages" },
  { href: "/contacts", label: "Contacts" },
  { href: "/settings", label: "Settings" },
];

// Extracted to "use client" so usePathname() works inside a Server Component layout
function AppNav() {
  "use client";
  const pathname = usePathname();

  return (
    <nav className="flex flex-col w-56 shrink-0 border-r px-4 py-6 gap-1">
      <span className="text-base font-semibold mb-4">InboxIQ</span>
      {NAV_LINKS.map((link) => {
        const active =
          link.href === "/"
            ? pathname === "/"
            : pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "text-sm px-3 py-2 rounded transition-colors",
              active
                ? "bg-accent font-medium text-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-foreground",
            )}
            aria-current={active ? "page" : undefined}
          >
            {link.label}
          </Link>
        );
      })}
      <div className="mt-auto pt-4 border-t">
        <SignOutButton />
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("font-sans", inter.variable)}>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased flex h-screen`}>
        <AppNav />
        <main className="flex-1 overflow-auto">
          <Providers>{children}</Providers>
        </main>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
```

**Note:** Inline `"use client"` on a function inside a Server Component file works in Next.js 14 as a nested client boundary. If you see a lint error, move `AppNav` to `frontend/components/AppNav.tsx` with `"use client"` at top and import it.

- [ ] **Step 2: Verify no TypeScript errors**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/layout.tsx
git commit -m "feat(nav): highlight active link using usePathname (#audit)"
```

---

## Task 13: Time-of-Day Greeting on Dashboard

**Files:**
- Modify: `frontend/app/page.tsx`

**Context:** The greeting is hardcoded to "Good morning" regardless of the time. Should vary: before noon → "Good morning", noon–17:00 → "Good afternoon", after 17:00 → "Good evening".

- [ ] **Step 1: Add a `greeting()` helper and update the JSX in `frontend/app/page.tsx`**

Add the helper function near the top of the file (after `firstName`):

```ts
function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}
```

Update the `<h1>` line:

```tsx
<h1 className="text-2xl font-semibold">
  {greeting()}, {firstName(user.data?.email)}
</h1>
```

- [ ] **Step 2: Verify no TypeScript errors**

```bash
cd frontend && npx tsc --noEmit
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/page.tsx
git commit -m "fix(dashboard): time-of-day greeting (morning/afternoon/evening) (#audit)"
```

---

## Task 14: Wire Re-Triage Job Polling After Context Switch

**Files:**
- Modify: `frontend/lib/queries/context-switch.ts`

**Context:** `PATCH /users/me/context` returns `{user, job_id, total}`. After this call succeeds, the frontend should poll `GET /jobs/{job_id}` every 2 seconds until `status === "done"` or `"failed"`, then invalidate the email query cache so the inbox refreshes with re-triaged results. Currently the inbox only auto-refreshes after its 30-second interval.

- [ ] **Step 1: Read the current implementation**

Open `frontend/lib/queries/context-switch.ts`. It likely uses `useMutation` with `onSuccess` that only invalidates `user-context`. We need to add polling after a successful context switch.

- [ ] **Step 2: Replace `frontend/lib/queries/context-switch.ts`**

```ts
"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiFetch } from "@/lib/api";
import type { User } from "@/types";

type UpdateContextResponse = {
  user: User;
  job_id: string;
  total: int;
};

type JobStatus = {
  status: "running" | "done" | "failed";
  processed: number;
  total: number;
};

async function pollJobUntilDone(
  jobId: string,
  onProgress?: (processed: number, total: number) => void,
): Promise<void> {
  const MAX_POLLS = 60;      // 60 × 2s = 2 minutes max
  const POLL_INTERVAL_MS = 2000;

  for (let i = 0; i < MAX_POLLS; i++) {
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
    try {
      const job = await apiFetch<JobStatus>(`/jobs/${jobId}`);
      onProgress?.(job.processed, job.total);
      if (job.status === "done" || job.status === "failed") return;
    } catch {
      // Server may return 404 if job expired — treat as done
      return;
    }
  }
}

export function useUpdateContext() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (context: User["default_context"]) =>
      apiFetch<UpdateContextResponse>("/users/me/context", {
        method: "PATCH",
        body: JSON.stringify({ context }),
      }),

    onSuccess: async (data) => {
      // Immediately update the user-context cache so the switcher shows the new value
      queryClient.setQueryData(["user-context"], data.user);

      // Poll until the retriage job completes, then refresh emails
      if (data.job_id && data.total > 0) {
        toast.info(`Re-triaging ${data.total} emails…`);
        await pollJobUntilDone(data.job_id);
        await queryClient.invalidateQueries({ queryKey: ["emails"] });
        await queryClient.invalidateQueries({ queryKey: ["email-counts"] });
        toast.success("Inbox updated for new context");
      }
    },

    onError: () => {
      toast.error("Failed to update context");
    },
  });
}
```

**Note:** `int` in the TypeScript type above is a typo — use `number`:

```ts
type UpdateContextResponse = {
  user: User;
  job_id: string;
  total: number;   // ← number, not int
};
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Run frontend tests (nothing new should break)**

```bash
cd frontend && npx vitest run --reporter=verbose
```

- [ ] **Step 5: Commit**

```bash
git add frontend/lib/queries/context-switch.ts
git commit -m "feat(inbox): poll retriage job after context switch, invalidate email cache when done (#audit)"
```

---

## Final Verification

After all tasks are committed:

- [ ] **Run complete backend test suite**

```bash
cd backend && python -m pytest --tb=short -q
```

Expected: all pass, no errors.

- [ ] **Run complete frontend test suite**

```bash
cd frontend && npx vitest run --reporter=verbose
```

Expected: all pass.

- [ ] **TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Smoke check**

```bash
# From repo root
bash scripts/smoke.sh
```

- [ ] **Create summary commit**

```bash
git commit --allow-empty -m "chore: all audit fixes complete — 14 tasks (#audit)"
```
