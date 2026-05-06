# Issue 1B: Gmail OAuth + Connected Accounts — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the full Gmail OAuth connect/disconnect flow — backend OAuth service, DB layer, two routers, and the `/settings` frontend page.

**Architecture:** Pure OAuth logic lives in `app/services/gmail_oauth.py` (no DB calls except inside `refresh_tokens`). The DB layer (`app/db/connected_accounts.py`) handles all Supabase queries via the service client, returning typed Pydantic models. Two routers (`auth.py` replaces stubs, `accounts.py` is new) wire the pieces together. The frontend `/settings` page reads connected accounts and drives the OAuth flow.

**Tech Stack:** FastAPI, PyJWT (HS256 state tokens), httpx (async Google API calls), respx (HTTP mocks in tests), Supabase Python client (sync, wrapped in `asyncio.to_thread`), Next.js 14 App Router, shadcn/ui, sonner, date-fns.

**Read first:** `plans/issue-1b-design.md` for full design rationale.

---

## File Map

| Action | Path |
|---|---|
| Create | `backend/supabase/migrations/007_schema_alignment.sql` |
| Create | `backend/app/models/connected_account.py` |
| Create | `backend/app/services/gmail_oauth.py` |
| Create | `backend/app/db/connected_accounts.py` |
| Modify | `backend/app/routers/auth.py` |
| Create | `backend/app/routers/accounts.py` |
| Modify | `backend/app/main.py` |
| Create | `backend/tests/services/__init__.py` |
| Create | `backend/tests/services/test_gmail_oauth.py` |
| Create | `backend/tests/routers/test_auth_oauth.py` |
| Create | `backend/tests/routers/test_accounts.py` |
| Modify | `frontend/app/layout.tsx` |
| Modify | `frontend/app/settings/page.tsx` |
| Create | `frontend/components/ui/alert-dialog.tsx` (via shadcn CLI) |

---

## Task 1: Migration 007 — schema alignment

**Files:**
- Create: `backend/supabase/migrations/007_schema_alignment.sql`

- [ ] **Step 1: Write the migration**

```sql
-- 007_schema_alignment.sql
-- Aligns connected_accounts with intended schema:
--   email → email_address, separate token cols → oauth_token JSONB,
--   adds disconnected_at / disconnected_reason

-- 1. Rename email → email_address
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'connected_accounts' AND column_name = 'email'
    ) THEN
        ALTER TABLE public.connected_accounts RENAME COLUMN email TO email_address;
    END IF;
END $$;

-- 2. Fix unique constraint
ALTER TABLE public.connected_accounts
    DROP CONSTRAINT IF EXISTS connected_accounts_user_id_email_key;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'connected_accounts_user_id_email_address_key'
    ) THEN
        ALTER TABLE public.connected_accounts
            ADD CONSTRAINT connected_accounts_user_id_email_address_key
            UNIQUE (user_id, email_address);
    END IF;
END $$;

-- 3. Add temp JSONB column
ALTER TABLE public.connected_accounts
    ADD COLUMN IF NOT EXISTS oauth_token_jsonb JSONB;

-- 4. Backfill from old columns (only while they still exist)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'connected_accounts' AND column_name = 'refresh_token'
    ) THEN
        UPDATE public.connected_accounts
        SET oauth_token_jsonb = json_build_object(
            'access_token',  COALESCE(oauth_token, ''),
            'refresh_token', COALESCE(refresh_token, ''),
            'expires_at',    COALESCE(token_expiry::text, now()::text),
            'scope',         'https://www.googleapis.com/auth/gmail.readonly'
        );
    END IF;
END $$;

-- 5. Drop the three old token columns
ALTER TABLE public.connected_accounts
    DROP COLUMN IF EXISTS refresh_token,
    DROP COLUMN IF EXISTS token_expiry;

-- Drop old TEXT oauth_token (before renaming the JSONB one)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'connected_accounts'
          AND column_name = 'oauth_token'
          AND data_type = 'text'
    ) THEN
        ALTER TABLE public.connected_accounts DROP COLUMN oauth_token;
    END IF;
END $$;

-- 6. Rename temp column to oauth_token
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'connected_accounts' AND column_name = 'oauth_token_jsonb'
    ) THEN
        ALTER TABLE public.connected_accounts
            RENAME COLUMN oauth_token_jsonb TO oauth_token;
    END IF;
END $$;

-- 7. Add disconnect tracking columns
ALTER TABLE public.connected_accounts
    ADD COLUMN IF NOT EXISTS disconnected_at     TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS disconnected_reason TEXT;
```

- [ ] **Step 2: Commit**

```bash
git add backend/supabase/migrations/007_schema_alignment.sql
git commit -m "feat(db): migration 007 — align connected_accounts schema"
```

---

## Task 2: Pydantic models for connected accounts

**Files:**
- Create: `backend/app/models/connected_account.py`

- [ ] **Step 1: Write the models file**

```python
# backend/app/models/connected_account.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OAuthTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: str


class ConnectedAccount(BaseModel):
    id: UUID
    user_id: UUID
    provider: str
    email_address: str
    oauth_token: OAuthTokens
    color: str | None = None
    last_synced: datetime | None = None
    disconnected_at: datetime | None = None
    disconnected_reason: str | None = None
    created_at: datetime


class AccountPublic(BaseModel):
    id: UUID
    email_address: str
    provider: str
    color: str | None = None
    last_synced: datetime | None = None
    disconnected_at: datetime | None = None
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/connected_account.py
git commit -m "feat(models): add OAuthTokens, ConnectedAccount, AccountPublic"
```

---

## Task 3: Gmail OAuth service — state JWT (TDD)

**Files:**
- Create: `backend/tests/services/__init__.py`
- Create: `backend/tests/services/test_gmail_oauth.py` (state JWT section)
- Create: `backend/app/services/gmail_oauth.py` (state functions + exceptions)

- [ ] **Step 1: Create tests/services package**

```bash
touch backend/tests/services/__init__.py
```

- [ ] **Step 2: Write failing tests for state JWT**

Create `backend/tests/services/test_gmail_oauth.py`:

```python
# backend/tests/services/test_gmail_oauth.py
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import jwt
import pytest
import respx

from app.models.connected_account import OAuthTokens
from app.services.gmail_oauth import (
    OAuthExchangeFailed,
    StateExpired,
    StateInvalid,
    _refresh_locks,
    build_authorize_url,
    exchange_code,
    refresh_tokens,
    sign_state,
    verify_state,
)


# --- State JWT ---

def test_sign_verify_state_roundtrip() -> None:
    user_id = uuid4()
    token = sign_state({"user_id": str(user_id), "return_to": "/settings"})
    claims = verify_state(token)
    assert claims.user_id == user_id
    assert claims.return_to == "/settings"


def test_verify_state_expired() -> None:
    payload = {
        "user_id": str(uuid4()),
        "return_to": "/settings",
        "nonce": "abc",
        "exp": (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp(),
    }
    token = jwt.encode(payload, "test-oauth-state-secret-at-least-32-chars!", algorithm="HS256")
    with pytest.raises(StateExpired):
        verify_state(token)


def test_verify_state_bad_signature() -> None:
    payload = {
        "user_id": str(uuid4()),
        "return_to": "/settings",
        "nonce": "abc",
        "exp": (datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp(),
    }
    token = jwt.encode(payload, "wrong-secret-here-at-least-32-chars!!", algorithm="HS256")
    with pytest.raises(StateInvalid):
        verify_state(token)
```

- [ ] **Step 3: Run tests — verify they fail with ImportError**

```bash
cd backend && python -m pytest tests/services/test_gmail_oauth.py -v 2>&1 | head -30
```

Expected: `ImportError` or `ModuleNotFoundError` (module doesn't exist yet).

- [ ] **Step 4: Write the service skeleton with state functions + exceptions**

Create `backend/app/services/gmail_oauth.py`:

```python
# backend/app/services/gmail_oauth.py
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
import jwt
from pydantic import BaseModel

from app.core.config import settings
from app.models.connected_account import OAuthTokens

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"

_refresh_locks: dict[UUID, asyncio.Lock] = {}


# --- Exceptions ---

class StateInvalid(Exception):
    pass


class StateExpired(Exception):
    pass


class OAuthExchangeFailed(Exception):
    pass


class RefreshFailed(Exception):
    def __init__(self, *, is_invalid_grant: bool) -> None:
        self.is_invalid_grant = is_invalid_grant
        super().__init__("Token refresh failed")


# --- State claim model ---

class StateClaims(BaseModel):
    user_id: UUID
    return_to: str
    nonce: str


# --- State signing ---

def sign_state(claims: dict) -> str:
    payload = {
        **claims,
        "nonce": uuid.uuid4().hex,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.oauth_state_secret, algorithm="HS256")


def verify_state(token: str) -> StateClaims:
    try:
        payload = jwt.decode(
            token,
            settings.oauth_state_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "user_id", "return_to", "nonce"]},
        )
        return StateClaims(**payload)
    except jwt.ExpiredSignatureError:
        raise StateExpired()
    except (jwt.PyJWTError, Exception):
        raise StateInvalid()


def build_authorize_url(user_id: UUID, return_to: str) -> str:
    raise NotImplementedError


async def exchange_code(code: str) -> OAuthTokens:
    raise NotImplementedError


async def get_gmail_address(access_token: str) -> str:
    raise NotImplementedError


async def refresh_tokens(account_id: UUID, refresh_token: str) -> OAuthTokens:
    raise NotImplementedError


async def revoke(refresh_token: str) -> None:
    raise NotImplementedError
```

- [ ] **Step 5: Run state JWT tests — verify they pass**

```bash
cd backend && python -m pytest tests/services/test_gmail_oauth.py::test_sign_verify_state_roundtrip tests/services/test_gmail_oauth.py::test_verify_state_expired tests/services/test_gmail_oauth.py::test_verify_state_bad_signature -v
```

Expected: 3 PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/tests/services/__init__.py backend/tests/services/test_gmail_oauth.py backend/app/services/gmail_oauth.py
git commit -m "feat(oauth): state JWT sign/verify with tests"
```

---

## Task 4: Gmail OAuth service — authorize URL, exchange_code, get_gmail_address (TDD)

**Files:**
- Modify: `backend/tests/services/test_gmail_oauth.py`
- Modify: `backend/app/services/gmail_oauth.py`

- [ ] **Step 1: Add failing tests to test_gmail_oauth.py**

Append to the existing test file after the state JWT tests:

```python
# --- build_authorize_url ---

import urllib.parse


def test_build_authorize_url_contains_required_params() -> None:
    user_id = uuid4()
    url = build_authorize_url(user_id, "/settings")
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert "accounts.google.com" in parsed.netloc
    assert params["client_id"][0] == "test-gmail-client-id.apps.googleusercontent.com"
    assert params["redirect_uri"][0] == "http://localhost:8000/auth/gmail/callback"
    assert params["response_type"][0] == "code"
    assert "https://www.googleapis.com/auth/gmail.readonly" in params["scope"][0]
    assert params["access_type"][0] == "offline"
    assert params["prompt"][0] == "consent"
    assert params["include_granted_scopes"][0] == "true"
    assert "state" in params


# --- exchange_code ---

@pytest.mark.asyncio
async def test_exchange_code_success() -> None:
    with respx.mock:
        respx.post(GOOGLE_TOKEN_URL).mock(
            return_value=httpx.Response(200, json={
                "access_token": "test_access",
                "refresh_token": "test_refresh",
                "expires_in": 3600,
                "scope": "https://www.googleapis.com/auth/gmail.readonly",
                "token_type": "Bearer",
            })
        )
        tokens = await exchange_code("auth_code_123")

    assert tokens.access_token == "test_access"
    assert tokens.refresh_token == "test_refresh"
    assert tokens.scope == "https://www.googleapis.com/auth/gmail.readonly"
    assert tokens.expires_at > datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_exchange_code_google_400_raises() -> None:
    with respx.mock:
        respx.post(GOOGLE_TOKEN_URL).mock(
            return_value=httpx.Response(400, json={"error": "invalid_grant"})
        )
        with pytest.raises(OAuthExchangeFailed):
            await exchange_code("bad_code")
```

You also need to add this import at the top of the test file (add to the existing import block):

```python
from app.services.gmail_oauth import GOOGLE_TOKEN_URL
```

- [ ] **Step 2: Run new tests — verify they fail**

```bash
cd backend && python -m pytest tests/services/test_gmail_oauth.py::test_build_authorize_url_contains_required_params tests/services/test_gmail_oauth.py::test_exchange_code_success tests/services/test_gmail_oauth.py::test_exchange_code_google_400_raises -v 2>&1 | tail -15
```

Expected: 3 FAILED (NotImplementedError).

- [ ] **Step 3: Implement build_authorize_url, exchange_code, get_gmail_address**

Replace the three stub functions in `backend/app/services/gmail_oauth.py`:

```python
def build_authorize_url(user_id: UUID, return_to: str) -> str:
    import urllib.parse
    params = {
        "client_id": settings.gmail_client_id,
        "redirect_uri": settings.gmail_redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": sign_state({"user_id": str(user_id), "return_to": return_to}),
    }
    return f"{GOOGLE_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


async def exchange_code(code: str) -> OAuthTokens:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "redirect_uri": settings.gmail_redirect_uri,
            },
        )
    if resp.status_code != 200:
        raise OAuthExchangeFailed(resp.text)
    data = resp.json()
    return OAuthTokens(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"]),
        scope=data.get("scope", ""),
    )


async def get_gmail_address(access_token: str) -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GMAIL_PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    resp.raise_for_status()
    return resp.json()["emailAddress"]
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/services/test_gmail_oauth.py -v -k "not refresh"
```

Expected: all PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/services/test_gmail_oauth.py backend/app/services/gmail_oauth.py
git commit -m "feat(oauth): build_authorize_url, exchange_code, get_gmail_address"
```

---

## Task 5: Gmail OAuth service — refresh_tokens lock + revoke (TDD)

**Files:**
- Modify: `backend/tests/services/test_gmail_oauth.py`
- Modify: `backend/app/services/gmail_oauth.py`

- [ ] **Step 1: Add the race test to test_gmail_oauth.py**

Append to the test file:

```python
# --- refresh_tokens race ---

@pytest.mark.asyncio
async def test_refresh_tokens_race_only_one_google_call() -> None:
    account_id = uuid4()
    _refresh_locks.pop(account_id, None)  # clean slate

    expired = OAuthTokens(
        access_token="old_access",
        refresh_token="old_refresh",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        scope="https://www.googleapis.com/auth/gmail.readonly",
    )
    fresh = OAuthTokens(
        access_token="new_access",
        refresh_token="old_refresh",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scope="https://www.googleapis.com/auth/gmail.readonly",
    )

    db_call_n = 0

    async def fake_get_account(aid: UUID):  # type: ignore[return]
        nonlocal db_call_n
        db_call_n += 1
        acct = MagicMock()
        # First call (inside lock for coro 1): expired.
        # Second call (inside lock for coro 2): fresh — already refreshed.
        acct.oauth_token = expired if db_call_n == 1 else fresh
        return acct

    google_calls = 0

    with (
        patch("app.services.gmail_oauth.get_account", side_effect=fake_get_account),
        patch("app.services.gmail_oauth.update_oauth_token", new_callable=AsyncMock),
    ):
        with respx.mock:
            def count_google(request: httpx.Request) -> httpx.Response:
                nonlocal google_calls
                google_calls += 1
                return httpx.Response(200, json={
                    "access_token": "new_access",
                    "expires_in": 3600,
                    "scope": "https://www.googleapis.com/auth/gmail.readonly",
                    "token_type": "Bearer",
                })

            respx.post(GOOGLE_TOKEN_URL).mock(side_effect=count_google)

            await asyncio.gather(
                refresh_tokens(account_id, "old_refresh"),
                refresh_tokens(account_id, "old_refresh"),
            )

    assert google_calls == 1, f"Expected 1 Google call, got {google_calls}"
```

- [ ] **Step 2: Run the race test — verify it fails**

```bash
cd backend && python -m pytest tests/services/test_gmail_oauth.py::test_refresh_tokens_race_only_one_google_call -v 2>&1 | tail -10
```

Expected: FAILED (NotImplementedError in refresh_tokens).

- [ ] **Step 3: Implement refresh_tokens and revoke**

Replace the two stub functions in `backend/app/services/gmail_oauth.py`:

```python
async def refresh_tokens(account_id: UUID, refresh_token: str) -> OAuthTokens:
    # Local import avoids circular dependency at module load time.
    from app.db.connected_accounts import get_account, update_oauth_token  # noqa: PLC0415

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
            raise RefreshFailed(is_invalid_grant=body.get("error") == "invalid_grant")

        data = resp.json()
        new_tokens = OAuthTokens(
            access_token=data["access_token"],
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"]),
            scope=data.get("scope", ""),
        )
        await update_oauth_token(account_id, new_tokens)
        return new_tokens


async def revoke(refresh_token: str) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_REVOKE_URL,
            params={"token": refresh_token},
        )
    if resp.status_code not in (200, 400):
        resp.raise_for_status()
```

- [ ] **Step 4: Run all service tests — verify all pass**

```bash
cd backend && python -m pytest tests/services/test_gmail_oauth.py -v
```

Expected: all PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/services/test_gmail_oauth.py backend/app/services/gmail_oauth.py
git commit -m "feat(oauth): refresh_tokens with lock, revoke, race test"
```

---

## Task 6: DB layer — connected_accounts

**Files:**
- Create: `backend/app/db/connected_accounts.py`

No unit tests here — the DB layer is tested implicitly through router tests (which mock these functions). Direct Supabase integration tests require a live DB.

- [ ] **Step 1: Write the DB layer**

```python
# backend/app/db/connected_accounts.py
from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import HTTPException

from app.db.supabase import get_service_client
from app.models.connected_account import ConnectedAccount, OAuthTokens


def _row_to_account(row: dict) -> ConnectedAccount:
    raw_token = row.get("oauth_token") or {}
    row = {**row, "oauth_token": OAuthTokens(**raw_token)}
    return ConnectedAccount(**row)


async def upsert_account(
    user_id: UUID,
    email_address: str,
    provider: str,
    oauth_token: OAuthTokens,
) -> ConnectedAccount:
    def _upsert() -> dict:
        client = get_service_client()
        result = client.table("connected_accounts").upsert(
            {
                "user_id": str(user_id),
                "email_address": email_address,
                "provider": provider,
                "oauth_token": oauth_token.model_dump(mode="json"),
                "disconnected_at": None,
                "disconnected_reason": None,
            },
            on_conflict="user_id,email_address",
        ).execute()
        row = result.data[0]
        if row.get("color") is None:
            client.rpc(
                "assign_account_color",
                {"p_user_id": str(user_id), "p_account_id": row["id"]},
            ).execute()
            row = (
                client.table("connected_accounts")
                .select("*")
                .eq("id", row["id"])
                .single()
                .execute()
                .data
            )
        return row

    row = await asyncio.to_thread(_upsert)
    return _row_to_account(row)


async def get_account(account_id: UUID) -> ConnectedAccount:
    def _fetch() -> dict | None:
        result = (
            get_service_client()
            .table("connected_accounts")
            .select("*")
            .eq("id", str(account_id))
            .maybe_single()
            .execute()
        )
        return result.data if result is not None else None  # type: ignore[return-value]

    row = await asyncio.to_thread(_fetch)
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    return _row_to_account(row)


async def list_user_accounts(user_id: UUID) -> list[ConnectedAccount]:
    def _fetch() -> list[dict]:
        result = (
            get_service_client()
            .table("connected_accounts")
            .select("*")
            .eq("user_id", str(user_id))
            .order("created_at")
            .execute()
        )
        return result.data or []

    rows = await asyncio.to_thread(_fetch)
    return [_row_to_account(r) for r in rows]


async def update_oauth_token(account_id: UUID, new_token: OAuthTokens) -> ConnectedAccount:
    def _update() -> dict:
        result = (
            get_service_client()
            .table("connected_accounts")
            .update({"oauth_token": new_token.model_dump(mode="json")})
            .eq("id", str(account_id))
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else {}

    row = await asyncio.to_thread(_update)
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    return _row_to_account(row)


async def mark_disconnected(account_id: UUID, reason: str) -> None:
    from datetime import datetime, timezone  # noqa: PLC0415

    def _update() -> None:
        get_service_client().table("connected_accounts").update(
            {
                "disconnected_at": datetime.now(timezone.utc).isoformat(),
                "disconnected_reason": reason,
            }
        ).eq("id", str(account_id)).execute()

    await asyncio.to_thread(_update)


async def delete_account(account_id: UUID) -> None:
    def _delete() -> None:
        get_service_client().table("connected_accounts").delete().eq(
            "id", str(account_id)
        ).execute()

    await asyncio.to_thread(_delete)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/db/connected_accounts.py
git commit -m "feat(db): connected_accounts CRUD layer"
```

---

## Task 7: Auth router — replace stubs (TDD)

**Files:**
- Create: `backend/tests/routers/test_auth_oauth.py`
- Modify: `backend/app/routers/auth.py`

- [ ] **Step 1: Write failing router tests**

Create `backend/tests/routers/test_auth_oauth.py`:

```python
# backend/tests/routers/test_auth_oauth.py
from __future__ import annotations

import urllib.parse
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.services.gmail_oauth import sign_state

_USER_ID = uuid4()
_EMAIL = "owner@example.com"


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email=_EMAIL)


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


# --- GET /auth/gmail/start ---

def test_start_returns_google_url(authed_client: TestClient) -> None:
    resp = authed_client.get("/auth/gmail/start?return_to=/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    parsed = urllib.parse.urlparse(data["url"])
    params = urllib.parse.parse_qs(parsed.query)
    assert "accounts.google.com" in parsed.netloc
    assert params["client_id"][0] == "test-gmail-client-id.apps.googleusercontent.com"
    assert params["response_type"][0] == "code"
    assert params["prompt"][0] == "consent"
    assert params["access_type"][0] == "offline"
    assert "state" in params


def test_start_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.get("/auth/gmail/start?return_to=/settings")
    assert resp.status_code == 401


# --- GET /auth/gmail/callback ---

def _mock_tokens() -> MagicMock:
    t = MagicMock()
    t.access_token = "acc"
    t.refresh_token = "ref"
    t.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    t.scope = "https://www.googleapis.com/auth/gmail.readonly"
    return t


def test_callback_success_redirects(anon_client: TestClient) -> None:
    state = sign_state({"user_id": str(_USER_ID), "return_to": "/settings"})
    with (
        patch("app.routers.auth.exchange_code", new_callable=AsyncMock, return_value=_mock_tokens()),
        patch("app.routers.auth.get_gmail_address", new_callable=AsyncMock, return_value="me@gmail.com"),
        patch("app.routers.auth.upsert_account", new_callable=AsyncMock),
    ):
        resp = anon_client.get(
            f"/auth/gmail/callback?code=good_code&state={state}",
            follow_redirects=False,
        )
    assert resp.status_code == 302
    loc = resp.headers["location"]
    assert "gmail_connected=success" in loc
    assert "/settings" in loc


def test_callback_expired_state(anon_client: TestClient) -> None:
    expired_state = jwt.encode(
        {
            "user_id": str(uuid4()),
            "return_to": "/settings",
            "nonce": "x",
            "exp": (datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp(),
        },
        "test-oauth-state-secret-at-least-32-chars!",
        algorithm="HS256",
    )
    resp = anon_client.get(
        f"/auth/gmail/callback?code=x&state={expired_state}",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "reason=state_expired" in resp.headers["location"]


def test_callback_bad_signature_state(anon_client: TestClient) -> None:
    bad_state = jwt.encode(
        {
            "user_id": str(uuid4()),
            "return_to": "/settings",
            "nonce": "x",
            "exp": (datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp(),
        },
        "totally-wrong-secret-at-least-32-chars!!",
        algorithm="HS256",
    )
    resp = anon_client.get(
        f"/auth/gmail/callback?code=x&state={bad_state}",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "reason=state_invalid" in resp.headers["location"]


def test_callback_user_cancelled(anon_client: TestClient) -> None:
    resp = anon_client.get(
        "/auth/gmail/callback?error=access_denied&state=irrelevant",
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "reason=user_cancelled" in resp.headers["location"]
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/routers/test_auth_oauth.py -v 2>&1 | tail -15
```

Expected: FAILED (endpoints return 501).

- [ ] **Step 3: Implement the auth router**

Replace all content of `backend/app/routers/auth.py`:

```python
# backend/app/routers/auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.core.auth import UserClaims, get_current_user
from app.core.config import settings
from app.db.connected_accounts import upsert_account
from app.services.gmail_oauth import (
    OAuthExchangeFailed,
    StateExpired,
    StateInvalid,
    build_authorize_url,
    exchange_code,
    get_gmail_address,
    verify_state,
)

router = APIRouter(prefix="/auth/gmail", tags=["gmail-auth"])


@router.get("/start")
async def gmail_oauth_start(
    return_to: str = "/settings",
    claims: UserClaims = Depends(get_current_user),
) -> dict[str, str]:
    url = build_authorize_url(claims.user_id, return_to)
    return {"url": url}


@router.get("/callback")
async def gmail_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    frontend = settings.frontend_url.rstrip("/")
    return_to = "/settings"

    def err(reason: str) -> RedirectResponse:
        return RedirectResponse(
            url=f"{frontend}{return_to}?gmail_connected=error&reason={reason}",
            status_code=302,
        )

    if error:
        return err("user_cancelled")

    if not state:
        return err("state_invalid")

    try:
        claims = verify_state(state)
        return_to = claims.return_to
    except StateExpired:
        return err("state_expired")
    except StateInvalid:
        return err("state_invalid")

    if not code:
        return err("exchange_failed")

    try:
        tokens = await exchange_code(code)
    except OAuthExchangeFailed:
        return err("exchange_failed")

    if not tokens.refresh_token:
        return err("no_refresh_token")

    email_address = await get_gmail_address(tokens.access_token)

    await upsert_account(
        user_id=claims.user_id,
        email_address=email_address,
        provider="gmail",
        oauth_token=tokens,
    )

    return RedirectResponse(
        url=f"{frontend}{return_to}?gmail_connected=success",
        status_code=302,
    )
```

- [ ] **Step 4: Run auth router tests — verify they pass**

```bash
cd backend && python -m pytest tests/routers/test_auth_oauth.py -v
```

Expected: all PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/routers/test_auth_oauth.py backend/app/routers/auth.py
git commit -m "feat(router): replace auth.py stubs, Gmail OAuth callback with tests"
```

---

## Task 8: Accounts router (TDD)

**Files:**
- Create: `backend/tests/routers/test_accounts.py`
- Create: `backend/app/routers/accounts.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing accounts tests**

Create `backend/tests/routers/test_accounts.py`:

```python
# backend/tests/routers/test_accounts.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app

_USER_ID = uuid4()
_EMAIL = "owner@example.com"


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email=_EMAIL)


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


def _make_account(user_id: UUID, account_id: UUID | None = None) -> MagicMock:
    a = MagicMock()
    a.id = account_id or uuid4()
    a.user_id = user_id
    a.email_address = "work@gmail.com"
    a.provider = "gmail"
    a.color = "#4F46E5"
    a.last_synced = None
    a.disconnected_at = None
    a.disconnected_reason = None
    a.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    a.oauth_token = MagicMock()
    a.oauth_token.refresh_token = "ref_tok"
    return a


# --- GET /accounts ---

def test_list_accounts_returns_own_only(authed_client: TestClient) -> None:
    acct = _make_account(_USER_ID)
    with patch("app.routers.accounts.list_user_accounts", new_callable=AsyncMock, return_value=[acct]):
        resp = authed_client.get("/accounts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["email_address"] == "work@gmail.com"


def test_list_accounts_no_oauth_token_in_response(authed_client: TestClient) -> None:
    acct = _make_account(_USER_ID)
    with patch("app.routers.accounts.list_user_accounts", new_callable=AsyncMock, return_value=[acct]):
        resp = authed_client.get("/accounts")
    assert resp.status_code == 200
    for item in resp.json():
        assert "oauth_token" not in item
        assert "access_token" not in item
        assert "refresh_token" not in item


def test_list_accounts_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.get("/accounts")
    assert resp.status_code == 401


# --- DELETE /accounts/{id} ---

def test_delete_account_as_owner(authed_client: TestClient) -> None:
    account_id = uuid4()
    acct = _make_account(_USER_ID, account_id)
    with (
        patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=acct),
        patch("app.routers.accounts.revoke", new_callable=AsyncMock),
        patch("app.routers.accounts.delete_account", new_callable=AsyncMock),
    ):
        resp = authed_client.delete(f"/accounts/{account_id}")
    assert resp.status_code == 204


def test_delete_account_wrong_user_returns_404(authed_client: TestClient) -> None:
    account_id = uuid4()
    other_user_id = uuid4()
    acct = _make_account(other_user_id, account_id)  # belongs to someone else
    with patch("app.routers.accounts.get_account", new_callable=AsyncMock, return_value=acct):
        resp = authed_client.delete(f"/accounts/{account_id}")
    assert resp.status_code == 404


def test_delete_account_requires_auth(anon_client: TestClient) -> None:
    resp = anon_client.delete(f"/accounts/{uuid4()}")
    assert resp.status_code == 401
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd backend && python -m pytest tests/routers/test_accounts.py -v 2>&1 | tail -15
```

Expected: FAILED (router not registered, 404 from FastAPI).

- [ ] **Step 3: Create the accounts router**

Create `backend/app/routers/accounts.py`:

```python
# backend/app/routers/accounts.py
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import UserClaims, get_current_user
from app.db.connected_accounts import delete_account, get_account, list_user_accounts
from app.models.connected_account import AccountPublic
from app.services.gmail_oauth import revoke

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(
    claims: UserClaims = Depends(get_current_user),
) -> list[AccountPublic]:
    accounts = await list_user_accounts(claims.user_id)
    return [
        AccountPublic(
            id=a.id,
            email_address=a.email_address,
            provider=a.provider,
            color=a.color,
            last_synced=a.last_synced,
            disconnected_at=a.disconnected_at,
        )
        for a in accounts
    ]


@router.delete("/{account_id}", status_code=204)
async def disconnect_account(
    account_id: UUID,
    claims: UserClaims = Depends(get_current_user),
) -> None:
    account = await get_account(account_id)
    if account.user_id != claims.user_id:
        raise HTTPException(status_code=404)
    try:
        await revoke(account.oauth_token.refresh_token)
    except Exception:
        pass
    await delete_account(account_id)
```

- [ ] **Step 4: Register the accounts router in main.py**

In `backend/app/main.py`, add the import and `include_router` call:

```python
# Add to existing imports block:
from app.routers import auth, users
# Change to:
from app.routers import accounts, auth, users
```

```python
# Add after the existing app.include_router(users.router) line:
app.include_router(accounts.router)
```

- [ ] **Step 5: Run all backend tests — verify they pass**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: all PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/tests/routers/test_accounts.py backend/app/routers/accounts.py backend/app/main.py
git commit -m "feat(router): accounts list + disconnect with tests"
```

---

## Task 9: Frontend — add Toaster and AlertDialog component

**Files:**
- Modify: `frontend/app/layout.tsx`
- Create: `frontend/components/ui/alert-dialog.tsx` (via shadcn)

- [ ] **Step 1: Add shadcn AlertDialog**

```bash
cd frontend && npx shadcn@latest add alert-dialog --yes
```

Expected: creates `frontend/components/ui/alert-dialog.tsx`.

- [ ] **Step 2: Add Toaster to layout.tsx**

The layout doesn't have a `<Toaster />` yet. Add it:

In `frontend/app/layout.tsx`, add the import at the top:
```typescript
import { Toaster } from "sonner";
```

Inside `<body>`, add `<Toaster />` just before the closing `</body>` tag:
```tsx
        <main className="flex-1 overflow-auto">{children}</main>
        <Toaster />
      </body>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/layout.tsx frontend/components/ui/alert-dialog.tsx
git commit -m "feat(frontend): add AlertDialog component and Toaster to layout"
```

---

## Task 10: Frontend — /settings page

**Files:**
- Modify: `frontend/app/settings/page.tsx`

- [ ] **Step 1: Write the settings page**

Replace all content of `frontend/app/settings/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

type Account = {
  id: string;
  email_address: string;
  provider: string;
  color: string | null;
  last_synced: string | null;
  disconnected_at: string | null;
};

export default function SettingsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [disconnecting, setDisconnecting] = useState<string | null>(null);
  const [confirmAccount, setConfirmAccount] = useState<Account | null>(null);

  // Handle OAuth callback query params
  useEffect(() => {
    const status = searchParams.get("gmail_connected");
    const reason = searchParams.get("reason");
    if (!status) return;

    if (status === "success") {
      toast.success("Gmail connected successfully.");
    } else {
      const messages: Record<string, string> = {
        user_cancelled: "Connection cancelled.",
        state_expired: "Session expired — please try again.",
        state_invalid: "Invalid OAuth state — please try again.",
        no_refresh_token: "No refresh token received. Revoke InboxIQ's Gmail access and reconnect.",
        exchange_failed: "OAuth code exchange failed. Please try again.",
      };
      toast.error(reason ? (messages[reason] ?? `Connection failed: ${reason}`) : "Connection failed.");
    }

    router.replace("/settings");
  }, [searchParams, router]);

  // Load connected accounts
  useEffect(() => {
    apiFetch<Account[]>("/accounts")
      .then(setAccounts)
      .catch(() => toast.error("Failed to load connected accounts."))
      .finally(() => setLoading(false));
  }, []);

  async function connectGmail() {
    try {
      const { url } = await apiFetch<{ url: string }>("/auth/gmail/start?return_to=/settings");
      window.location.href = url;
    } catch {
      toast.error("Could not start Gmail connection. Is the API running?");
    }
  }

  async function confirmDisconnect() {
    if (!confirmAccount) return;
    const { id, email_address } = confirmAccount;
    setConfirmAccount(null);
    setDisconnecting(id);
    setAccounts((prev) => prev.filter((a) => a.id !== id));
    try {
      await apiFetch(`/accounts/${id}`, { method: "DELETE" });
      toast.success(`Disconnected ${email_address}.`);
    } catch {
      toast.error(`Failed to disconnect ${email_address}. Please try again.`);
      // Re-fetch to restore state
      apiFetch<Account[]>("/accounts").then(setAccounts).catch(() => null);
    } finally {
      setDisconnecting(null);
    }
  }

  return (
    <div className="p-6 max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <Button onClick={() => void connectGmail()}>Connect Gmail</Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading accounts…</p>
      ) : accounts.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No accounts connected. Click Connect Gmail to get started.
        </p>
      ) : (
        <ul className="space-y-3">
          {accounts.map((account) => (
            <li
              key={account.id}
              className="flex items-center justify-between rounded-lg border bg-card px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <span
                  className="h-3 w-3 rounded-full shrink-0"
                  style={{ backgroundColor: account.color ?? "#94a3b8" }}
                />
                <div>
                  <p className="text-sm font-medium">{account.email_address}</p>
                  <p className="text-xs text-muted-foreground">
                    {account.last_synced
                      ? `Last synced ${formatDistanceToNow(new Date(account.last_synced))} ago`
                      : "Never synced"}
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                disabled={disconnecting === account.id}
                onClick={() => setConfirmAccount(account)}
              >
                {disconnecting === account.id ? "Disconnecting…" : "Disconnect"}
              </Button>
            </li>
          ))}
        </ul>
      )}

      <AlertDialog open={!!confirmAccount} onOpenChange={(open) => { if (!open) setConfirmAccount(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disconnect account?</AlertDialogTitle>
            <AlertDialogDescription>
              This will revoke InboxIQ&apos;s access to{" "}
              <strong>{confirmAccount?.email_address}</strong> and delete all
              synced emails for this account.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => void confirmDisconnect()}>
              Disconnect
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/settings/page.tsx
git commit -m "feat(settings): connected accounts UI with connect/disconnect flow"
```

---

## Task 11: Verification

**Files:** none

- [ ] **Step 1: Security grep — confirm no token fields in frontend**

```bash
grep -rn "oauth_token\|access_token\|refresh_token" \
  frontend/app frontend/lib frontend/components
```

Expected: zero matches. If any appear, remove them before continuing.

- [ ] **Step 2: Run all backend tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: all PASSED. Fix any failures before continuing.

- [ ] **Step 3: Type-check backend**

```bash
cd backend && mypy app/
```

Expected: no errors (or only pre-existing ones unrelated to this issue).

- [ ] **Step 4: Type-check frontend**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 5: Start dev servers and manually test Connect Gmail flow**

```bash
cd /path/to/repo && make dev
```

Walk through manually:
1. Sign in, navigate to `/settings`
2. Click **Connect Gmail** — should redirect to Google consent screen
3. Complete consent — should redirect back to `/settings?gmail_connected=success`
4. Verify toast appears: "Gmail connected successfully."
5. Verify account row appears with email, color dot, "Never synced"
6. Click **Disconnect** → confirm dialog → account removed from list

- [ ] **Step 6: Take screenshot**

Save screenshot of `/settings` showing connected account to `plans/issue-1b-screenshot.png`.

- [ ] **Step 7: Final commit**

```bash
git add plans/issue-1b-screenshot.png
git commit -m "docs: add issue-1b settings screenshot"
```
