# Issue 1C — Gmail Sync, Email List API, Scheduler, Basic Inbox Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Gmail message sync (per-account background job + on-demand), the `/emails` list API with cursor pagination, and a minimal `/inbox` frontend page.

**Architecture:** A `gmail_sync` service handles all Gmail API interaction (auth, message fetch, body parsing) and writes emails via `db/emails.py`. A manual trigger endpoint (`POST /accounts/{id}/sync`) and APScheduler background job both call `sync_account`. The `/emails` endpoint returns paginated email rows with joined account color. The frontend `/inbox` page renders the list and a "Sync now" button.

**Tech Stack:** FastAPI + Pydantic v2 + httpx + google-api-python-client + APScheduler 3.10 + BeautifulSoup4 + supabase-py (all already in requirements.txt); Next.js 14 App Router + TypeScript + Tailwind + shadcn/ui on the frontend.

---

## File Map

**New files:**
- `backend/supabase/migrations/008_last_synced_is_archived.sql` — adds `last_synced` to `connected_accounts`, `is_archived` to `emails`
- `backend/supabase/migrations/009_upsert_email_fn.sql` — PostgreSQL function for atomic upsert with insert/update detection
- `backend/app/models/email.py` — `ParsedEmail`, `Email`, `SyncResult`, `EmailListPage`, `EmailFilters`
- `backend/app/services/gmail_sync.py` — Gmail API interaction: auth, message list, body parse, sync orchestration
- `backend/app/db/emails.py` — `upsert_email`, `list_emails`, `get_email`
- `backend/app/routers/emails.py` — `GET /emails` with cursor pagination
- `backend/app/tasks/scheduler.py` — APScheduler background job (every 5 min)
- `backend/tests/fixtures/gmail/plain_text.json` — Gmail API message fixture
- `backend/tests/fixtures/gmail/html_only.json`
- `backend/tests/fixtures/gmail/multipart_alternative.json`
- `backend/tests/fixtures/gmail/multipart_mixed.json`
- `backend/tests/fixtures/gmail/multipart_related.json`
- `backend/tests/fixtures/gmail/nested_multipart.json`
- `backend/tests/fixtures/gmail/image_only.json`
- `backend/tests/services/test_gmail_sync.py`
- `backend/tests/routers/test_emails.py`

**Modified files:**
- `backend/app/db/connected_accounts.py` — add `update_last_synced`, `list_accounts_due_for_sync`
- `backend/app/routers/accounts.py` — add `POST /accounts/{id}/sync`
- `backend/app/main.py` — add emails router, wire scheduler into lifespan
- `frontend/app/inbox/page.tsx` — minimal inbox UI
- `frontend/types/index.ts` — update `Email` type

---

## DB Column Reference

**`connected_accounts`** (after migrations 007 + 008):
`id, user_id, provider, email_address, oauth_token (JSONB), color, last_synced, disconnected_at, disconnected_reason, created_at`

**`emails`** (after migrations 003 + 008):
`id, user_id, account_id, gmail_id, thread_id, subject, sender, snippet, body_text, received_at, is_read, labels, ai_summary, ai_category, is_archived, created_at`
Unique constraint: `(account_id, gmail_id)`

---

## Task 1: Migrations 008 + 009

**Files:**
- Create: `backend/supabase/migrations/008_last_synced_is_archived.sql`
- Create: `backend/supabase/migrations/009_upsert_email_fn.sql`

- [ ] **Step 1: Create migration 008**

```sql
-- 008_last_synced_is_archived.sql
-- Adds last_synced to connected_accounts and is_archived to emails

ALTER TABLE public.connected_accounts
    ADD COLUMN IF NOT EXISTS last_synced TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS connected_accounts_last_synced_idx
    ON public.connected_accounts(last_synced);

ALTER TABLE public.emails
    ADD COLUMN IF NOT EXISTS is_archived BOOLEAN NOT NULL DEFAULT false;
```

Write this to `backend/supabase/migrations/008_last_synced_is_archived.sql`.

- [ ] **Step 2: Create migration 009**

```sql
-- 009_upsert_email_fn.sql
-- Atomic email upsert with insert/update detection via xmax trick

CREATE OR REPLACE FUNCTION public.upsert_email_record(
    p_account_id  UUID,
    p_user_id     UUID,
    p_gmail_id    TEXT,
    p_subject     TEXT,
    p_sender      TEXT,
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
    INSERT INTO public.emails
        (account_id, user_id, gmail_id, subject, sender, body_text, received_at)
    VALUES
        (p_account_id, p_user_id, p_gmail_id, p_subject, p_sender, p_body_text, p_received_at)
    ON CONFLICT (account_id, gmail_id) DO UPDATE SET
        subject    = EXCLUDED.subject,
        body_text  = EXCLUDED.body_text,
        sender     = EXCLUDED.sender
    RETURNING (xmax = 0) INTO _is_insert;

    RETURN CASE WHEN _is_insert THEN 'inserted' ELSE 'updated' END;
END;
$$;
```

Write this to `backend/supabase/migrations/009_upsert_email_fn.sql`.

- [ ] **Step 3: Commit**

```bash
git add backend/supabase/migrations/008_last_synced_is_archived.sql \
        backend/supabase/migrations/009_upsert_email_fn.sql
git commit -m "feat(db): add last_synced, is_archived columns + upsert_email_record fn (#1c)"
```

---

## Task 2: Pydantic Models — `app/models/email.py`

**Files:**
- Create: `backend/app/models/email.py`

- [ ] **Step 1: Write failing test** (verifies model imports and shapes)

Create `backend/tests/test_email_models.py`:

```python
# backend/tests/test_email_models.py
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.email import Email, EmailFilters, EmailListPage, ParsedEmail, SyncResult


def test_parsed_email_fields() -> None:
    p = ParsedEmail(
        external_id="abc123",
        sender_email="alice@example.com",
        subject="Hello",
        body_preview="Body text here",
        received_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    assert p.external_id == "abc123"
    assert p.sender_email == "alice@example.com"


def test_sync_result_defaults() -> None:
    r = SyncResult(fetched=10, inserted=8, updated=2, errors=0)
    assert r.fetched == 10


def test_email_filters_defaults() -> None:
    f = EmailFilters(user_id=uuid4())
    assert f.limit == 50
    assert f.is_archived is False
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && python -m pytest tests/test_email_models.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.models.email'`

- [ ] **Step 3: Create `backend/app/models/email.py`**

```python
# backend/app/models/email.py
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class ParsedEmail(BaseModel):
    external_id: str          # maps to emails.gmail_id
    sender_email: str         # maps to emails.sender (always lowercased)
    subject: str
    body_preview: str         # maps to emails.body_text
    received_at: datetime


class SyncResult(BaseModel):
    fetched: int
    inserted: int
    updated: int
    errors: int


class Email(BaseModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    gmail_id: str
    thread_id: str | None = None
    subject: str | None = None
    sender: str | None = None
    received_at: datetime | None = None
    is_read: bool = False
    labels: list[str] = []
    ai_summary: str | None = None
    ai_category: str | None = None
    is_archived: bool = False
    account_color: str | None = None
    created_at: datetime


class EmailListPage(BaseModel):
    items: list[Email]
    next_cursor: str | None


class EmailFilters(BaseModel):
    user_id: UUID
    account_id: UUID | None = None
    triage_category: str | None = None   # maps to ai_category
    is_archived: bool = False
    since: datetime | None = None
    search: str | None = None
    cursor: str | None = None
    limit: int = 50
```

- [ ] **Step 4: Run to verify tests pass**

```bash
python -m pytest tests/test_email_models.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/email.py backend/tests/test_email_models.py
git commit -m "feat(models): add Email, ParsedEmail, SyncResult, EmailFilters models (#1c)"
```

---

## Task 3: DB Layer Additions — `connected_accounts.py`

**Files:**
- Modify: `backend/app/db/connected_accounts.py`

- [ ] **Step 1: Write failing tests**

Append to `backend/tests/test_email_models.py` (or create a separate file — add to existing is fine):

Create `backend/tests/db/test_connected_accounts_sync.py`:

```python
# backend/tests/db/test_connected_accounts_sync.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.db.connected_accounts import list_accounts_due_for_sync, update_last_synced


@pytest.mark.asyncio
async def test_update_last_synced_calls_supabase() -> None:
    account_id = uuid4()
    now = datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc)

    mock_client = MagicMock()
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

    with patch("app.db.connected_accounts.get_service_client", return_value=mock_client):
        await update_last_synced(account_id, now)

    mock_client.table.assert_called_with("connected_accounts")
    mock_client.table().update.assert_called_once_with({"last_synced": now.isoformat()})


@pytest.mark.asyncio
async def test_list_accounts_due_for_sync_returns_list() -> None:
    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.is_.return_value.or_.return_value.execute.return_value.data = []

    with patch("app.db.connected_accounts.get_service_client", return_value=mock_client):
        result = await list_accounts_due_for_sync()

    assert result == []
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/db/test_connected_accounts_sync.py -v
```
Expected: `ImportError: cannot import name 'list_accounts_due_for_sync'`

- [ ] **Step 3: Create `backend/tests/db/__init__.py`**

```bash
touch backend/tests/db/__init__.py
```

- [ ] **Step 4: Add functions to `backend/app/db/connected_accounts.py`**

Add these imports at the top (if not present):
```python
from datetime import timedelta
```

Append to the file:

```python
async def update_last_synced(account_id: UUID, synced_at: datetime) -> None:
    def _update() -> None:
        get_service_client().table("connected_accounts").update(
            {"last_synced": synced_at.isoformat()}
        ).eq("id", str(account_id)).execute()

    await asyncio.to_thread(_update)


async def list_accounts_due_for_sync() -> list[ConnectedAccount]:
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=14)).isoformat()

    def _fetch() -> list[dict[str, Any]]:
        result = (
            get_service_client()
            .table("connected_accounts")
            .select("*")
            .is_("disconnected_at", "null")
            .or_(f"last_synced.is.null,last_synced.lt.{cutoff}")
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [_row_to_account(r) for r in rows]
```

Also add `timedelta` to the existing `from datetime import datetime, timezone` import:

```python
from datetime import datetime, timedelta, timezone
```

- [ ] **Step 5: Run to verify tests pass**

```bash
python -m pytest tests/db/test_connected_accounts_sync.py -v
```
Expected: 2 passed.

- [ ] **Step 6: Run full suite to verify no regressions**

```bash
python -m pytest -v
```
Expected: all existing tests + 2 new = green.

- [ ] **Step 7: Commit**

```bash
git add backend/app/db/connected_accounts.py \
        backend/tests/db/__init__.py \
        backend/tests/db/test_connected_accounts_sync.py
git commit -m "feat(db): add update_last_synced and list_accounts_due_for_sync (#1c)"
```

---

## Task 4: Gmail JSON Test Fixtures

**Files:**
- Create: `backend/tests/fixtures/gmail/` (directory + 7 files)

These fixtures simulate the Gmail API `messages.get(format="full")` response shape. Bodies are base64url-encoded. Run the Python snippet below to produce the fixture files — it encodes content correctly.

- [ ] **Step 1: Create fixture directory and `__init__.py`**

```bash
mkdir -p backend/tests/fixtures/gmail
touch backend/tests/fixtures/__init__.py
touch backend/tests/fixtures/gmail/__init__.py
```

- [ ] **Step 2: Generate fixture files with a helper script**

Run this Python script from the `backend/` directory to produce all 7 fixture files:

```python
# Run from: backend/
import base64, json, os

def b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()

fixtures_dir = "tests/fixtures/gmail"

def make_headers(from_: str = "Alice <alice@example.com>", subject: str = "Test Subject"):
    return [
        {"name": "From", "value": from_},
        {"name": "Subject", "value": subject},
        {"name": "Date", "value": "Wed, 1 Jan 2025 12:00:00 +0000"},
    ]

# 1. plain_text.json
plain_text = {
    "id": "msg_plain",
    "threadId": "thread_plain",
    "internalDate": "1735732800000",
    "payload": {
        "mimeType": "text/plain",
        "headers": make_headers(subject="Plain Text Email"),
        "body": {"size": 17, "data": b64("Hello plain world")},
        "parts": [],
    },
}

# 2. html_only.json
html_only = {
    "id": "msg_html",
    "threadId": "thread_html",
    "internalDate": "1735732800000",
    "payload": {
        "mimeType": "text/html",
        "headers": make_headers(subject="HTML Only Email"),
        "body": {"size": 27, "data": b64("<p>Hello <b>HTML</b> world</p>")},
        "parts": [],
    },
}

# 3. multipart_alternative.json — text/plain preferred over text/html
multipart_alternative = {
    "id": "msg_alt",
    "threadId": "thread_alt",
    "internalDate": "1735732800000",
    "payload": {
        "mimeType": "multipart/alternative",
        "headers": make_headers(subject="Multipart Alternative"),
        "body": {"size": 0},
        "parts": [
            {
                "mimeType": "text/plain",
                "headers": [],
                "body": {"size": 11, "data": b64("Hello plain")},
            },
            {
                "mimeType": "text/html",
                "headers": [],
                "body": {"size": 22, "data": b64("<p>Hello HTML</p>")},
            },
        ],
    },
}

# 4. multipart_mixed.json — text + attachment (PDF ignored)
multipart_mixed = {
    "id": "msg_mixed",
    "threadId": "thread_mixed",
    "internalDate": "1735732800000",
    "payload": {
        "mimeType": "multipart/mixed",
        "headers": make_headers(subject="With Attachment"),
        "body": {"size": 0},
        "parts": [
            {
                "mimeType": "text/plain",
                "headers": [],
                "body": {"size": 20, "data": b64("Email with attachment")},
            },
            {
                "mimeType": "application/pdf",
                "headers": [{"name": "Content-Disposition", "value": "attachment; filename=doc.pdf"}],
                "body": {"size": 1000, "data": ""},
            },
        ],
    },
}

# 5. multipart_related.json — html + inline image
multipart_related = {
    "id": "msg_related",
    "threadId": "thread_related",
    "internalDate": "1735732800000",
    "payload": {
        "mimeType": "multipart/related",
        "headers": make_headers(subject="HTML with Inline Image"),
        "body": {"size": 0},
        "parts": [
            {
                "mimeType": "text/html",
                "headers": [],
                "body": {"size": 30, "data": b64("<p>Email with image</p>")},
            },
            {
                "mimeType": "image/png",
                "headers": [{"name": "Content-ID", "value": "<img001>"}],
                "body": {"size": 500, "data": ""},
            },
        ],
    },
}

# 6. nested_multipart.json — mixed → alternative → text/html
nested_multipart = {
    "id": "msg_nested",
    "threadId": "thread_nested",
    "internalDate": "1735732800000",
    "payload": {
        "mimeType": "multipart/mixed",
        "headers": make_headers(subject="Nested Multipart"),
        "body": {"size": 0},
        "parts": [
            {
                "mimeType": "multipart/alternative",
                "headers": [],
                "body": {"size": 0},
                "parts": [
                    {
                        "mimeType": "text/html",
                        "headers": [],
                        "body": {"size": 25, "data": b64("<p>Deeply nested HTML</p>")},
                    }
                ],
            }
        ],
    },
}

# 7. image_only.json — no text part at all
image_only = {
    "id": "msg_image",
    "threadId": "thread_image",
    "internalDate": "1735732800000",
    "payload": {
        "mimeType": "multipart/related",
        "headers": make_headers(subject="Image Only"),
        "body": {"size": 0},
        "parts": [
            {
                "mimeType": "image/jpeg",
                "headers": [],
                "body": {"size": 2048, "data": ""},
            }
        ],
    },
}

fixtures = {
    "plain_text.json": plain_text,
    "html_only.json": html_only,
    "multipart_alternative.json": multipart_alternative,
    "multipart_mixed.json": multipart_mixed,
    "multipart_related.json": multipart_related,
    "nested_multipart.json": nested_multipart,
    "image_only.json": image_only,
}

for filename, data in fixtures.items():
    path = os.path.join(fixtures_dir, filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {path}")
```

Run: `cd backend && python generate_fixtures.py` then delete the script.

- [ ] **Step 3: Verify fixture files exist**

```bash
ls backend/tests/fixtures/gmail/
```
Expected: 7 .json files listed.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/fixtures/
git commit -m "test(gmail): add Gmail API response fixtures for parse_payload tests (#1c)"
```

---

## Task 5: TDD `parse_payload` — Gmail Sync Service (Part 1)

**Files:**
- Create: `backend/app/services/gmail_sync.py` (parse_payload only in this task)
- Create: `backend/tests/services/test_gmail_sync.py` (parse_payload tests only)

- [ ] **Step 1: Write failing tests for `parse_payload`**

Create `backend/tests/services/test_gmail_sync.py`:

```python
# backend/tests/services/test_gmail_sync.py
from __future__ import annotations

import json
import os

import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "gmail")


def load(name: str) -> dict:
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


def test_parse_payload_plain_text() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("plain_text.json")
    result = parse_payload(msg["payload"])
    assert result == "Hello plain world"


def test_parse_payload_html_only_strips_tags() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("html_only.json")
    result = parse_payload(msg["payload"])
    assert "<p>" not in result
    assert "<b>" not in result
    assert "Hello" in result
    assert "HTML" in result
    assert "world" in result


def test_parse_payload_multipart_alternative_prefers_plain() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("multipart_alternative.json")
    result = parse_payload(msg["payload"])
    assert result == "Hello plain"


def test_parse_payload_multipart_mixed_returns_text_ignores_attachment() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("multipart_mixed.json")
    result = parse_payload(msg["payload"])
    assert result == "Email with attachment"


def test_parse_payload_multipart_related_returns_html_text() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("multipart_related.json")
    result = parse_payload(msg["payload"])
    assert "Email with image" in result
    assert "<p>" not in result


def test_parse_payload_nested_multipart_extracts_html_text() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("nested_multipart.json")
    result = parse_payload(msg["payload"])
    assert "Deeply nested HTML" in result
    assert "<p>" not in result


def test_parse_payload_image_only_returns_empty_string() -> None:
    from app.services.gmail_sync import parse_payload
    msg = load("image_only.json")
    result = parse_payload(msg["payload"])
    assert result == ""


def test_parse_payload_truncates_to_2000_chars() -> None:
    import base64
    from app.services.gmail_sync import BODY_PREVIEW_MAX_CHARS, parse_payload
    long_text = "x" * 5000
    data = base64.urlsafe_b64encode(long_text.encode()).decode()
    payload = {
        "mimeType": "text/plain",
        "headers": [],
        "body": {"size": 5000, "data": data},
        "parts": [],
    }
    result = parse_payload(payload)
    assert len(result) == BODY_PREVIEW_MAX_CHARS
    assert BODY_PREVIEW_MAX_CHARS == 2000
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/services/test_gmail_sync.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.services.gmail_sync'`

- [ ] **Step 3: Create `backend/app/services/gmail_sync.py` with `parse_payload` + constants**

```python
# backend/app/services/gmail_sync.py
from __future__ import annotations

import asyncio
import base64
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID

from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.db.connected_accounts import (
    get_account,
    mark_disconnected,
    update_last_synced,
)
from app.db.emails import upsert_email
from app.models.connected_account import ConnectedAccount
from app.models.email import ParsedEmail, SyncResult
from app.services.gmail_oauth import RefreshFailed, refresh_tokens

logger = logging.getLogger(__name__)

INITIAL_SYNC_LIMIT = 50
BODY_PREVIEW_MAX_CHARS = 2000
PER_ACCOUNT_CONCURRENCY = 5


def _extract(payload: dict) -> tuple[str, str]:
    """Recursively extract (plain_text, html_text) from a Gmail message payload."""
    mime_type = payload.get("mimeType", "")
    parts = payload.get("parts") or []

    if parts:
        plain_parts: list[str] = []
        html_parts: list[str] = []
        for part in parts:
            p, h = _extract(part)
            if p:
                plain_parts.append(p)
            if h:
                html_parts.append(h)
        return " ".join(plain_parts), " ".join(html_parts)

    body_data = payload.get("body", {}).get("data", "")
    if not body_data:
        return "", ""

    # Gmail uses base64url without padding — add it back
    remainder = len(body_data) % 4
    if remainder:
        body_data += "=" * (4 - remainder)
    try:
        decoded = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
    except Exception:
        return "", ""

    if mime_type == "text/plain":
        return decoded.strip(), ""
    if mime_type == "text/html":
        soup = BeautifulSoup(decoded, "html.parser")
        text = " ".join(soup.get_text(" ").split())
        return "", text
    return "", ""


def parse_payload(payload: dict) -> str:
    plain, html = _extract(payload)
    text = plain or html
    return text[:BODY_PREVIEW_MAX_CHARS]
```

- [ ] **Step 4: Run to verify tests pass**

```bash
python -m pytest tests/services/test_gmail_sync.py -v
```
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/gmail_sync.py \
        backend/tests/services/test_gmail_sync.py
git commit -m "feat(sync): implement parse_payload with TDD (#1c)"
```

---

## Task 6: TDD `sync_account` — Gmail Sync Service (Part 2)

**Files:**
- Modify: `backend/app/services/gmail_sync.py` — add remaining functions
- Modify: `backend/tests/services/test_gmail_sync.py` — add sync_account tests

The full gmail_sync.py requires these functions after parse_payload:
- `get_authed_service(account)` — builds an authenticated Gmail service object
- `list_message_ids(service, after_unix_seconds)` — lists message IDs, paginates
- `fetch_message(service, message_id)` — fetches full message, returns ParsedEmail | None
- `sync_account(account_id)` — orchestrates the full sync loop

- [ ] **Step 1: Add sync_account tests to the test file**

Append to `backend/tests/services/test_gmail_sync.py`:

```python
# --- sync_account integration tests ---

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


def _make_connected_account(user_id=None, last_synced=None, disconnected_at=None):
    from datetime import datetime, timezone
    from app.models.connected_account import ConnectedAccount, OAuthTokens
    return ConnectedAccount(
        id=uuid4(),
        user_id=user_id or uuid4(),
        provider="gmail",
        email_address="test@gmail.com",
        oauth_token=OAuthTokens(
            access_token="acc",
            refresh_token="ref",
            expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            scope="https://www.googleapis.com/auth/gmail.readonly",
        ),
        color="#4F46E5",
        last_synced=last_synced,
        disconnected_at=disconnected_at,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


def _make_parsed_email(external_id: str = "msg1"):
    from datetime import datetime, timezone
    from app.models.email import ParsedEmail
    return ParsedEmail(
        external_id=external_id,
        sender_email="sender@example.com",
        subject="Test",
        body_preview="Body",
        received_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
async def test_sync_account_inserts_messages() -> None:
    from app.services.gmail_sync import sync_account

    account = _make_connected_account()
    parsed = _make_parsed_email("msg1")

    with (
        patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.services.gmail_sync.get_authed_service", new_callable=AsyncMock, return_value=MagicMock()),
        patch("app.services.gmail_sync.list_message_ids", new_callable=AsyncMock, return_value=["msg1"]),
        patch("app.services.gmail_sync.fetch_message", new_callable=AsyncMock, return_value=parsed),
        patch("app.services.gmail_sync.upsert_email", new_callable=AsyncMock, return_value="inserted"),
        patch("app.services.gmail_sync.update_last_synced", new_callable=AsyncMock),
    ):
        result = await sync_account(account.id)

    assert result.fetched == 1
    assert result.inserted == 1
    assert result.updated == 0
    assert result.errors == 0


@pytest.mark.asyncio
async def test_sync_account_skips_disconnected() -> None:
    from datetime import datetime, timezone
    from app.services.gmail_sync import sync_account

    account = _make_connected_account(disconnected_at=datetime(2025, 1, 1, tzinfo=timezone.utc))

    with patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account):
        result = await sync_account(account.id)

    assert result.fetched == 0
    assert result.errors == 0


@pytest.mark.asyncio
async def test_sync_account_skips_404_messages() -> None:
    from app.services.gmail_sync import sync_account

    account = _make_connected_account()

    with (
        patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.services.gmail_sync.get_authed_service", new_callable=AsyncMock, return_value=MagicMock()),
        patch("app.services.gmail_sync.list_message_ids", new_callable=AsyncMock, return_value=["msg1", "msg2"]),
        patch("app.services.gmail_sync.fetch_message", new_callable=AsyncMock, side_effect=[None, _make_parsed_email("msg2")]),
        patch("app.services.gmail_sync.upsert_email", new_callable=AsyncMock, return_value="inserted"),
        patch("app.services.gmail_sync.update_last_synced", new_callable=AsyncMock),
    ):
        result = await sync_account(account.id)

    assert result.fetched == 2
    assert result.inserted == 1


@pytest.mark.asyncio
async def test_sync_account_invalid_grant_marks_disconnected() -> None:
    from app.services.gmail_sync import sync_account
    from app.services.gmail_oauth import RefreshFailed

    account = _make_connected_account()

    with (
        patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.services.gmail_sync.get_authed_service", new_callable=AsyncMock,
              side_effect=RefreshFailed(is_invalid_grant=True)),
        patch("app.services.gmail_sync.mark_disconnected", new_callable=AsyncMock) as mock_mark,
    ):
        result = await sync_account(account.id)

    mock_mark.assert_awaited_once_with(account.id, "invalid_grant")
    assert result.errors > 0


@pytest.mark.asyncio
async def test_sync_account_idempotent_second_run_produces_zero_inserts() -> None:
    from app.services.gmail_sync import sync_account

    account = _make_connected_account()
    parsed = _make_parsed_email("msg1")

    shared_patches = dict(
        get_account=AsyncMock(return_value=account),
        get_authed_service=AsyncMock(return_value=MagicMock()),
        list_message_ids=AsyncMock(return_value=["msg1"]),
        fetch_message=AsyncMock(return_value=parsed),
        update_last_synced=AsyncMock(),
    )

    with (
        patch("app.services.gmail_sync.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.services.gmail_sync.get_authed_service", new_callable=AsyncMock, return_value=MagicMock()),
        patch("app.services.gmail_sync.list_message_ids", new_callable=AsyncMock, return_value=["msg1"]),
        patch("app.services.gmail_sync.fetch_message", new_callable=AsyncMock, return_value=parsed),
        patch("app.services.gmail_sync.upsert_email", new_callable=AsyncMock, return_value="updated"),
        patch("app.services.gmail_sync.update_last_synced", new_callable=AsyncMock),
    ):
        result = await sync_account(account.id)

    assert result.inserted == 0
    assert result.updated == 1
```

- [ ] **Step 2: Run to verify tests fail**

```bash
python -m pytest tests/services/test_gmail_sync.py::test_sync_account_inserts_messages -v
```
Expected: `ImportError` on `get_authed_service` or similar.

- [ ] **Step 3: Add remaining functions to `backend/app/services/gmail_sync.py`**

Append after `parse_payload`:

```python

async def get_authed_service(account: ConnectedAccount):
    tokens = account.oauth_token
    if tokens.expires_at < datetime.now(timezone.utc) + timedelta(seconds=60):
        tokens = await refresh_tokens(account.id, tokens.refresh_token)

    creds = Credentials(token=tokens.access_token)

    def _build():
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    return await asyncio.to_thread(_build)


async def list_message_ids(service, after_unix_seconds: int | None) -> list[str]:
    def _list() -> list[str]:
        ids: list[str] = []
        kwargs: dict = {"userId": "me"}
        if after_unix_seconds is None:
            kwargs["maxResults"] = INITIAL_SYNC_LIMIT
        else:
            kwargs["q"] = f"after:{after_unix_seconds}"

        while True:
            resp = service.users().messages().list(**kwargs).execute()
            ids.extend(m["id"] for m in resp.get("messages", []))
            page_token = resp.get("nextPageToken")
            if not page_token or after_unix_seconds is None:
                break
            kwargs["pageToken"] = page_token

        return ids

    return await asyncio.to_thread(_list)


_SENDER_RE = re.compile(r"<([^>]+)>")


async def fetch_message(service, message_id: str) -> ParsedEmail | None:
    def _get() -> dict | None:
        try:
            return (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except HttpError as exc:
            if exc.resp.status == 404:
                return None
            raise

    msg = await asyncio.to_thread(_get)
    if msg is None:
        return None

    payload = msg.get("payload", {})
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

    subject = headers.get("Subject", "")
    from_header = headers.get("From", "")
    m = _SENDER_RE.search(from_header)
    sender_email = (m.group(1) if m else from_header).lower()

    internal_date_ms = msg.get("internalDate")
    if internal_date_ms:
        received_at = datetime.fromtimestamp(
            int(internal_date_ms) / 1000, tz=timezone.utc
        )
    else:
        received_at = datetime.now(timezone.utc)

    body_preview = parse_payload(payload)

    return ParsedEmail(
        external_id=message_id,
        sender_email=sender_email,
        subject=subject,
        body_preview=body_preview,
        received_at=received_at,
    )


async def sync_account(account_id: UUID) -> SyncResult:
    account = await get_account(account_id)

    if account.disconnected_at is not None:
        return SyncResult(fetched=0, inserted=0, updated=0, errors=0)

    sync_started_at = datetime.now(timezone.utc)

    try:
        service = await get_authed_service(account)
    except RefreshFailed as exc:
        if exc.is_invalid_grant:
            await mark_disconnected(account_id, "invalid_grant")
        return SyncResult(fetched=0, inserted=0, updated=0, errors=1)

    after = (
        int(account.last_synced.timestamp()) if account.last_synced else None
    )

    message_ids = await list_message_ids(service, after)
    semaphore = asyncio.Semaphore(PER_ACCOUNT_CONCURRENCY)

    async def process(mid: str) -> tuple[Literal["inserted", "updated", "skipped"], str]:
        async with semaphore:
            parsed = await fetch_message(service, mid)
            if parsed is None:
                return ("skipped", mid)
            outcome = await upsert_email(account_id, account.user_id, parsed)
            return (outcome, mid)

    results = await asyncio.gather(
        *[process(m) for m in message_ids], return_exceptions=True
    )

    inserted = updated = errors = 0
    for r in results:
        if isinstance(r, Exception):
            logger.error("sync_account error for account %s: %s", account_id, r)
            errors += 1
        elif r[0] == "inserted":
            inserted += 1
        elif r[0] == "updated":
            updated += 1

    if errors == 0:
        await update_last_synced(account_id, sync_started_at)

    return SyncResult(
        fetched=len(message_ids),
        inserted=inserted,
        updated=updated,
        errors=errors,
    )
```

- [ ] **Step 4: Run to verify all sync tests pass**

```bash
python -m pytest tests/services/test_gmail_sync.py -v
```
Expected: 13 passed (8 parse_payload + 5 sync_account).

- [ ] **Step 5: Run full suite**

```bash
python -m pytest -v
```
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/gmail_sync.py \
        backend/tests/services/test_gmail_sync.py
git commit -m "feat(sync): implement sync_account, fetch_message, list_message_ids with TDD (#1c)"
```

---

## Task 7: TDD Emails DB Layer — `app/db/emails.py`

**Files:**
- Create: `backend/app/db/emails.py`
- Create: `backend/tests/db/test_emails.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/db/test_emails.py`:

```python
# backend/tests/db/test_emails.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.email import EmailFilters, ParsedEmail


@pytest.mark.asyncio
async def test_upsert_email_calls_rpc_and_returns_inserted() -> None:
    from app.db.emails import upsert_email

    account_id = uuid4()
    user_id = uuid4()
    parsed = ParsedEmail(
        external_id="gmail123",
        sender_email="alice@example.com",
        subject="Hello",
        body_preview="Body",
        received_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
    )

    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.return_value.data = "inserted"

    with patch("app.db.emails.get_service_client", return_value=mock_client):
        result = await upsert_email(account_id, user_id, parsed)

    assert result == "inserted"
    mock_client.rpc.assert_called_once_with(
        "upsert_email_record",
        {
            "p_account_id": str(account_id),
            "p_user_id": str(user_id),
            "p_gmail_id": "gmail123",
            "p_subject": "Hello",
            "p_sender": "alice@example.com",
            "p_body_text": "Body",
            "p_received_at": "2025-06-01T00:00:00+00:00",
        },
    )


@pytest.mark.asyncio
async def test_list_emails_returns_empty_for_no_results() -> None:
    from app.db.emails import list_emails

    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

    with patch("app.db.emails.get_service_client", return_value=mock_client):
        result = await list_emails(EmailFilters(user_id=uuid4()))

    assert result.items == []
    assert result.next_cursor is None


@pytest.mark.asyncio
async def test_get_email_returns_none_for_missing() -> None:
    from app.db.emails import get_email

    mock_client = MagicMock()
    mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None

    with patch("app.db.emails.get_service_client", return_value=mock_client):
        result = await get_email(uuid4(), uuid4())

    assert result is None
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/db/test_emails.py -v
```
Expected: `ModuleNotFoundError: No module named 'app.db.emails'`

- [ ] **Step 3: Create `backend/app/db/emails.py`**

```python
# backend/app/db/emails.py
from __future__ import annotations

import asyncio
import base64
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from app.db.supabase import get_service_client
from app.models.email import Email, EmailFilters, EmailListPage, ParsedEmail


def _cursor_encode(received_at: datetime, email_id: UUID) -> str:
    raw = f"{received_at.isoformat()}|{email_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _cursor_decode(cursor: str) -> tuple[str, str]:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    rt, eid = raw.split("|", 1)
    return rt, eid


def _row_to_email(row: dict[str, Any]) -> Email:
    nested = row.pop("connected_accounts", None) or {}
    account_color = nested.get("color") if isinstance(nested, dict) else None
    return Email(**row, account_color=account_color)


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
                "p_body_text": parsed.body_preview,
                "p_received_at": parsed.received_at.isoformat(),
            },
        ).execute()
        return result.data  # "inserted" or "updated"

    return await asyncio.to_thread(_do)  # type: ignore[return-value]


async def list_emails(filters: EmailFilters) -> EmailListPage:
    limit = min(filters.limit, 100)

    def _fetch() -> list[dict[str, Any]]:
        q = (
            get_service_client()
            .table("emails")
            .select("*, connected_accounts(color)")
            .eq("user_id", str(filters.user_id))
            .eq("is_archived", filters.is_archived)
        )

        if filters.account_id:
            q = q.eq("account_id", str(filters.account_id))

        if filters.triage_category:
            q = q.eq("ai_category", filters.triage_category)

        if filters.since:
            q = q.gte("received_at", filters.since.isoformat())

        if filters.search:
            q = q.ilike("subject", f"%{filters.search}%")

        if filters.cursor:
            rt, eid = _cursor_decode(filters.cursor)
            q = q.or_(f"received_at.lt.{rt},and(received_at.eq.{rt},id.lt.{eid})")

        q = q.order("received_at", desc=True).order("id", desc=True).limit(limit + 1)
        return q.execute().data or []

    rows = await asyncio.to_thread(_fetch)

    has_more = len(rows) > limit
    page_rows = rows[:limit]
    items = [_row_to_email(r) for r in page_rows]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        if last.received_at:
            next_cursor = _cursor_encode(last.received_at, last.id)

    return EmailListPage(items=items, next_cursor=next_cursor)


async def get_email(email_id: UUID, user_id: UUID) -> Email | None:
    def _fetch() -> dict[str, Any] | None:
        result = (
            get_service_client()
            .table("emails")
            .select("*, connected_accounts(color)")
            .eq("id", str(email_id))
            .eq("user_id", str(user_id))
            .maybe_single()
            .execute()
        )
        return result.data

    row = await asyncio.to_thread(_fetch)
    if not row:
        return None
    return _row_to_email(row)
```

- [ ] **Step 4: Run to verify tests pass**

```bash
python -m pytest tests/db/test_emails.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Run full suite**

```bash
python -m pytest -v
```
Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add backend/app/db/emails.py backend/tests/db/test_emails.py
git commit -m "feat(db): add emails DB layer with upsert, list (cursor paging), get (#1c)"
```

---

## Task 8: TDD Emails Router — `app/routers/emails.py`

**Files:**
- Create: `backend/app/routers/emails.py`
- Create: `backend/tests/routers/test_emails.py`
- Modify: `backend/app/main.py` — register emails router

- [ ] **Step 1: Write failing tests**

Create `backend/tests/routers/test_emails.py`:

```python
# backend/tests/routers/test_emails.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.email import Email, EmailListPage

_USER_ID = uuid4()


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email="user@example.com")


def _make_email(user_id=None) -> Email:
    return Email(
        id=uuid4(),
        user_id=user_id or _USER_ID,
        account_id=uuid4(),
        gmail_id="msg1",
        subject="Hello",
        sender="alice@example.com",
        received_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        is_read=False,
        labels=[],
        is_archived=False,
        account_color="#4F46E5",
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client() -> TestClient:
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_list_emails_returns_200_with_items(authed_client: TestClient) -> None:
    page = EmailListPage(items=[_make_email()], next_cursor=None)
    with patch("app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page):
        resp = authed_client.get("/emails")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["next_cursor"] is None


def test_list_emails_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.get("/emails")
    assert resp.status_code == 401


def test_list_emails_no_oauth_token_in_response(authed_client: TestClient) -> None:
    page = EmailListPage(items=[_make_email()], next_cursor=None)
    with patch("app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page):
        resp = authed_client.get("/emails")
    for item in resp.json()["items"]:
        assert "oauth_token" not in item
        assert "access_token" not in item
        assert "refresh_token" not in item


def test_list_emails_rls_isolation(authed_client: TestClient) -> None:
    other_user_email = _make_email(user_id=uuid4())
    page = EmailListPage(items=[other_user_email], next_cursor=None)
    with patch("app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page) as mock_list:
        resp = authed_client.get("/emails")
    # The router must pass the current user's ID to list_emails, not trust the request
    call_filters = mock_list.call_args[0][0]
    assert call_filters.user_id == _USER_ID


def test_list_emails_with_cursor(authed_client: TestClient) -> None:
    page = EmailListPage(items=[], next_cursor="abc123")
    with patch("app.routers.emails.list_emails", new_callable=AsyncMock, return_value=page):
        resp = authed_client.get("/emails?cursor=some_cursor&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["next_cursor"] == "abc123"
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/routers/test_emails.py -v
```
Expected: fails with 404 on `/emails` (router not registered) or import error.

- [ ] **Step 3: Create `backend/app/routers/emails.py`**

```python
# backend/app/routers/emails.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.auth import UserClaims, get_current_user
from app.db.emails import list_emails
from app.models.email import EmailFilters, EmailListPage

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("")
async def get_emails(
    claims: UserClaims = Depends(get_current_user),
    account_id: str | None = Query(default=None),
    triage_category: str | None = Query(default=None),
    is_archived: bool = Query(default=False),
    since: str | None = Query(default=None),
    search: str | None = Query(default=None),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
) -> EmailListPage:
    from datetime import datetime

    filters = EmailFilters(
        user_id=claims.user_id,
        account_id=account_id,  # type: ignore[arg-type]
        triage_category=triage_category,
        is_archived=is_archived,
        since=datetime.fromisoformat(since) if since else None,
        search=search,
        cursor=cursor,
        limit=limit,
    )
    return await list_emails(filters)
```

- [ ] **Step 4: Register the emails router in `backend/app/main.py`**

Change:
```python
from app.routers import accounts, auth, users
```
To:
```python
from app.routers import accounts, auth, emails, users
```

Add after `app.include_router(accounts.router)`:
```python
app.include_router(emails.router)
```

- [ ] **Step 5: Run to verify tests pass**

```bash
python -m pytest tests/routers/test_emails.py -v
```
Expected: 5 passed.

- [ ] **Step 6: Run full suite**

```bash
python -m pytest -v
```
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/emails.py \
        backend/app/main.py \
        backend/tests/routers/test_emails.py
git commit -m "feat(emails): add GET /emails router with cursor pagination (#1c)"
```

---

## Task 9: TDD Accounts Router Extension — `POST /accounts/{id}/sync`

**Files:**
- Modify: `backend/app/routers/accounts.py`
- Create: `backend/tests/routers/test_accounts_sync.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/routers/test_accounts_sync.py`:

```python
# backend/tests/routers/test_accounts_sync.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.connected_account import ConnectedAccount, OAuthTokens
from app.models.email import SyncResult

_USER_ID = uuid4()


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email="user@example.com")


def _make_account(disconnected_at=None) -> ConnectedAccount:
    return ConnectedAccount(
        id=uuid4(),
        user_id=_USER_ID,
        provider="gmail",
        email_address="work@gmail.com",
        oauth_token=OAuthTokens(
            access_token="acc",
            refresh_token="ref",
            expires_at=datetime(2099, 1, 1, tzinfo=timezone.utc),
            scope="https://www.googleapis.com/auth/gmail.readonly",
        ),
        color="#4F46E5",
        disconnected_at=disconnected_at,
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def anon_client() -> TestClient:
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_sync_account_returns_sync_result(authed_client: TestClient) -> None:
    account = _make_account()
    sync_result = SyncResult(fetched=5, inserted=5, updated=0, errors=0)

    with (
        patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=account),
        patch("app.routers.accounts.sync_account", new_callable=AsyncMock, return_value=sync_result),
    ):
        resp = authed_client.post(f"/accounts/{account.id}/sync")

    assert resp.status_code == 200
    data = resp.json()
    assert data["fetched"] == 5
    assert data["inserted"] == 5


def test_sync_wrong_user_returns_404(authed_client: TestClient) -> None:
    account = _make_account()
    account = account.model_copy(update={"user_id": uuid4()})  # different user

    with patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=account):
        resp = authed_client.post(f"/accounts/{account.id}/sync")

    assert resp.status_code == 404


def test_sync_disconnected_account_returns_409(authed_client: TestClient) -> None:
    account = _make_account(disconnected_at=datetime(2025, 1, 1, tzinfo=timezone.utc))

    with patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=account):
        resp = authed_client.post(f"/accounts/{account.id}/sync")

    assert resp.status_code == 409
    assert resp.json()["reason"] == "disconnected"


def test_sync_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.post(f"/accounts/{uuid4()}/sync")
    assert resp.status_code == 401
```

- [ ] **Step 2: Run to verify it fails**

```bash
python -m pytest tests/routers/test_accounts_sync.py -v
```
Expected: 404 responses (route not found) or import errors.

- [ ] **Step 3: Extend `backend/app/routers/accounts.py`**

Add imports at the top:
```python
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse

from app.core.auth import UserClaims, get_current_user
from app.db.connected_accounts import delete_account, get_account, list_user_accounts
from app.models.connected_account import AccountPublic
from app.models.email import SyncResult
from app.services.gmail_oauth import revoke
from app.services.gmail_sync import sync_account
```

Note: Replace the existing import block at the top of accounts.py with the above (adding `JSONResponse`, `SyncResult`, `sync_account`).

Append the new endpoint to the router (after `disconnect_account`):

```python

@router.post("/{account_id}/sync")
async def trigger_sync(
    account_id: UUID,
    claims: UserClaims = Depends(get_current_user),
) -> SyncResult:
    account = await get_account(account_id)
    if account.user_id != claims.user_id:
        raise HTTPException(status_code=404)
    if account.disconnected_at is not None:
        raise HTTPException(
            status_code=409,
            detail={"reason": "disconnected"},
        )
    return await sync_account(account_id)
```

- [ ] **Step 4: Fix the 409 detail format**

FastAPI serializes `detail` as-is. The test checks `resp.json()["reason"]`. For a dict `detail`, FastAPI wraps it in `{"detail": {...}}`. Update the test to check correctly, OR change the endpoint to return a JSONResponse:

Instead of `raise HTTPException(status_code=409, detail={"reason": "disconnected"})`, use:

```python
    if account.disconnected_at is not None:
        return JSONResponse(
            status_code=409,
            content={"reason": "disconnected"},
        )
```

Update `backend/app/routers/accounts.py` accordingly and ensure `JSONResponse` is imported.

- [ ] **Step 5: Run to verify tests pass**

```bash
python -m pytest tests/routers/test_accounts_sync.py -v
```
Expected: 4 passed.

- [ ] **Step 6: Run full suite**

```bash
python -m pytest -v
```
Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/accounts.py \
        backend/tests/routers/test_accounts_sync.py
git commit -m "feat(accounts): add POST /accounts/{id}/sync endpoint (#1c)"
```

---

## Task 10: Scheduler — `app/tasks/scheduler.py` + `main.py` Wiring

**Files:**
- Create: `backend/app/tasks/scheduler.py`
- Modify: `backend/app/main.py`

No unit tests for the scheduler itself (it's integration-level). The scheduler is tested implicitly when `make dev` runs.

- [ ] **Step 1: Create `backend/app/tasks/scheduler.py`**

```python
# backend/app/tasks/scheduler.py
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.connected_accounts import list_accounts_due_for_sync
from app.services.gmail_sync import sync_account

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

_GLOBAL_SYNC_CONCURRENCY = 10


@scheduler.scheduled_job("interval", minutes=5, id="sync_all_due_accounts")
async def sync_all_due_accounts() -> None:
    import time
    start = time.monotonic()
    logger.info("scheduler job_start sync_all_due_accounts")

    accounts = await list_accounts_due_for_sync()
    semaphore = asyncio.Semaphore(_GLOBAL_SYNC_CONCURRENCY)

    async def _sync_one(account_id):
        async with semaphore:
            try:
                result = await sync_account(account_id)
                return result
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
```

- [ ] **Step 2: Wire scheduler into `backend/app/main.py` lifespan**

Replace the lifespan function:

```python
from app.tasks.scheduler import scheduler

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    for var in _REQUIRED_ENV_VARS:
        logger.info("env %s present=%s", var, bool(os.getenv(var)))
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
```

- [ ] **Step 3: Run full test suite to verify no breakage**

```bash
python -m pytest -v
```
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add backend/app/tasks/scheduler.py backend/app/main.py
git commit -m "feat(scheduler): add APScheduler 5-min sync job wired into lifespan (#1c)"
```

---

## Task 11: Frontend — Minimal `/inbox` Page

**Files:**
- Modify: `frontend/app/inbox/page.tsx`
- Modify: `frontend/types/index.ts`

- [ ] **Step 1: Update `frontend/types/index.ts` — add `account_color` to Email type**

Replace the existing `Email` type in `frontend/types/index.ts`:

```typescript
export type Email = {
  id: string;
  user_id: string;
  account_id: string;
  gmail_id: string;
  thread_id: string | null;
  subject: string | null;
  sender: string | null;
  received_at: string | null;
  is_read: boolean;
  labels: string[];
  ai_summary: string | null;
  ai_category: string | null;
  is_archived: boolean;
  account_color: string | null;
  created_at: string;
};

export type EmailListPage = {
  items: Email[];
  next_cursor: string | null;
};
```

- [ ] **Step 2: Read `frontend/app/inbox/page.tsx` then replace with the new implementation**

First read the existing file, then write:

```typescript
"use client";

import { useEffect, useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import type { ConnectedAccount, EmailListPage } from "@/types";

export default function InboxPage() {
  const [emails, setEmails] = useState<EmailListPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  async function fetchEmails() {
    setLoading(true);
    try {
      const page = await apiFetch<EmailListPage>("/emails");
      setEmails(page);
    } catch {
      toast.error("Failed to load emails");
    } finally {
      setLoading(false);
    }
  }

  async function syncNow() {
    setSyncing(true);
    try {
      const accounts = await apiFetch<ConnectedAccount[]>("/accounts");
      await Promise.all(
        accounts.map((a) => apiFetch(`/accounts/${a.id}/sync`, { method: "POST" }))
      );
      await fetchEmails();
    } catch {
      toast.error("Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    void fetchEmails();
  }, []);

  return (
    <main className="p-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Inbox</h1>
        <Button onClick={syncNow} disabled={syncing}>
          {syncing ? "Syncing..." : "Sync now"}
        </Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : emails && emails.items.length > 0 ? (
        <ul className="space-y-1">
          {emails.items.map((email) => (
            <li
              key={email.id}
              className="flex items-center gap-3 rounded-lg border px-4 py-3 text-sm"
            >
              <span
                className="h-2.5 w-2.5 rounded-full shrink-0"
                style={{ backgroundColor: email.account_color ?? "#6b7280" }}
              />
              <span className="font-medium shrink-0 w-48 truncate">
                {email.sender ?? "(unknown)"}
              </span>
              <span className="flex-1 truncate text-muted-foreground">
                {email.subject ?? "(no subject)"}
              </span>
              <span className="text-xs text-muted-foreground shrink-0">
                {email.received_at
                  ? formatDistanceToNow(new Date(email.received_at), { addSuffix: true })
                  : ""}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">
          No emails yet — click Sync now.
        </p>
      )}
    </main>
  );
}
```

- [ ] **Step 3: Type-check**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no errors.

- [ ] **Step 4: Commit**

```bash
cd ..
git add frontend/app/inbox/page.tsx frontend/types/index.ts
git commit -m "feat(frontend): implement minimal /inbox page with sync button (#1c)"
```

---

## Self-Review Checklist

After all tasks are committed, run:

```bash
cd backend && python -m pytest -v
```
Expected: all tests green.

```bash
cd ../frontend && npx tsc --noEmit
```
Expected: no type errors.

Security grep (must return zero Gmail-token matches in frontend):
```bash
grep -rn "oauth_token\|refresh_token" frontend/app frontend/lib frontend/components
```
Expected: no matches (the existing `access_token` in `api.ts` and `inbox-home.tsx` are Supabase JWT tokens, not Gmail tokens — acceptable).

---

## Verification Steps (Manual — after `make dev`)

1. `make test` — confirm green
2. `make dev` — start backend + frontend
3. Navigate to `/settings`, click Connect Gmail, complete OAuth
4. Navigate to `/inbox`, click "Sync now"
5. Confirm `/inbox` shows ≥10 emails
6. Click "Sync now" again — confirm count stays the same (idempotent)
7. Send yourself a new email, wait 30 sec, sync again — confirm count +1
8. Screenshot the `/inbox` page showing ≥10 emails; save to `plans/issue-1c-screenshot.png`
