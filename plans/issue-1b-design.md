# Issue 1B Design: Gmail OAuth + Connected Accounts

**Date:** 2026-05-05
**Branch:** issue-1b-gmail-oauth

---

## Overview

Implements the full Gmail OAuth connect/disconnect flow plus the connected-accounts management UI. Builds on Issue 1A (auth, users, route stubs). Delivers: backend OAuth service, DB layer for connected accounts, two routers, and the `/settings` frontend page.

---

## 1. Database — migration 007

File: `backend/supabase/migrations/007_schema_alignment.sql`

The existing `002_connected_accounts` schema has three mismatches with the intended design:

| 002 column | Change |
|---|---|
| `email TEXT` | Rename → `email_address` |
| `oauth_token TEXT` + `refresh_token TEXT` + `token_expiry TIMESTAMPTZ` | Collapse → `oauth_token JSONB` |
| (missing) | Add `disconnected_at TIMESTAMPTZ` |
| (missing) | Add `disconnected_reason TEXT` |

Migration steps (all guarded with `IF EXISTS` / `IF NOT EXISTS` for idempotency):

1. Rename `email` → `email_address` (skip if column `email_address` already exists)
2. Drop old unique constraint `(user_id, email)`, recreate as `(user_id, email_address)`
3. Add temp column `oauth_token_jsonb JSONB`
4. Backfill: `UPDATE SET oauth_token_jsonb = json_build_object('access_token', oauth_token, 'refresh_token', refresh_token, 'expires_at', token_expiry, 'scope', 'https://www.googleapis.com/auth/gmail.readonly')` (references the old TEXT `oauth_token` column before it is dropped)
5. Drop old columns: `oauth_token` (TEXT), `refresh_token`, `token_expiry`
6. Rename `oauth_token_jsonb` → `oauth_token`
7. Add `disconnected_at TIMESTAMPTZ` (nullable)
8. Add `disconnected_reason TEXT` (nullable)

This ordering avoids naming conflicts between the old TEXT `oauth_token` column and the new JSONB column.

---

## 2. Backend service — `app/services/gmail_oauth.py`

Pure OAuth logic. No DB calls in this layer.

### Constants
```
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
```

### Pydantic models
- `StateClaims(user_id, return_to, nonce, exp)` — decoded state JWT payload
- `OAuthTokens(access_token, refresh_token, expires_at: datetime, scope)` — stored in `oauth_token JSONB`

### Custom exceptions
- `StateInvalid` — bad signature or malformed
- `StateExpired` — valid signature but `exp` in the past
- `OAuthExchangeFailed` — Google returned a non-200 on code exchange
- `RefreshFailed(is_invalid_grant: bool)` — token refresh failed; `is_invalid_grant=True` when Google returns `invalid_grant` (account should be marked disconnected)

### Functions

**`sign_state(claims: dict) -> str`**
HS256 JWT signed with `settings.oauth_state_secret`. Adds `nonce=uuid4().hex` and `exp=now+600s`. Returns encoded token string.

**`verify_state(token: str) -> StateClaims`**
Decodes and validates signature + expiry. Raises `StateExpired` on expired token, `StateInvalid` on bad signature or malformed payload.

**`build_authorize_url(user_id: UUID, return_to: str) -> str`**
Assembles Google OAuth URL with query params:
- `client_id`, `redirect_uri` (from settings)
- `response_type=code`, `scope` (space-joined SCOPES)
- `access_type=offline`, `prompt=consent` (always — ensures refresh_token is issued)
- `include_granted_scopes=true`
- `state=<sign_state({user_id, return_to})>`

**`exchange_code(code: str) -> OAuthTokens`**
POSTs to `GOOGLE_TOKEN_URL` with `grant_type=authorization_code`, code, client_id, client_secret, redirect_uri. Parses response into `OAuthTokens`; `expires_at = now() + expires_in`. Raises `OAuthExchangeFailed` on non-200.

**`_refresh_locks: dict[UUID, asyncio.Lock]`** — module-level dict.

**`refresh_tokens(account_id: UUID, refresh_token: str) -> OAuthTokens`**
1. Acquires `_refresh_locks[account_id]` (creates Lock if not present).
2. Inside lock: re-reads `oauth_token` from DB.
3. If `expires_at > now() + 60s`, returns current tokens without calling Google (another worker already refreshed).
4. Otherwise: POSTs `grant_type=refresh_token` to Google, writes new `OAuthTokens` to DB via `update_oauth_token`, returns new tokens.
5. On `invalid_grant` from Google: raises `RefreshFailed(is_invalid_grant=True)`.

**`revoke(refresh_token: str) -> None`**
POSTs to `GOOGLE_REVOKE_URL`. Swallows HTTP 400 (already revoked). Raises on other errors.

---

## 3. DB layer — `app/db/connected_accounts.py`

All queries via `get_service_client()`. Returns typed Pydantic models.

### `ConnectedAccount` model
```python
class ConnectedAccount(BaseModel):
    id: UUID
    user_id: UUID
    provider: str
    email_address: str
    oauth_token: OAuthTokens
    color: str | None
    last_synced: datetime | None
    disconnected_at: datetime | None
    disconnected_reason: str | None
    created_at: datetime
```

### Functions

**`upsert_account(user_id, email_address, provider, oauth_token) -> ConnectedAccount`**
`ON CONFLICT (user_id, email_address) DO UPDATE SET oauth_token = EXCLUDED.oauth_token, disconnected_at = NULL, disconnected_reason = NULL`. After upsert, calls `assign_account_color(user_id, account_id)` only when the returned row has `color IS NULL` (new inserts only — reconnects preserve the existing color).

**`get_account(account_id: UUID) -> ConnectedAccount`**
Raises 404 if not found.

**`list_user_accounts(user_id: UUID) -> list[ConnectedAccount]`**
Ordered by `created_at ASC`.

**`update_oauth_token(account_id: UUID, new_token: OAuthTokens) -> ConnectedAccount`**
Single UPDATE, returns updated row.

**`mark_disconnected(account_id: UUID, reason: str) -> None`**
Sets `disconnected_at = now()`, `disconnected_reason = reason`.

**`delete_account(account_id: UUID) -> None`**
DELETE by id. Cascade in DB removes associated emails.

---

## 4. Routers

### `app/routers/auth.py` (replaces stubs)

**`GET /auth/gmail/start?return_to=/settings`** — requires `get_current_user`
- Calls `build_authorize_url(user_id, return_to)`.
- Returns `{"url": "<google authorize url>"}`.
- Frontend does `window.location.href = url`.

**`GET /auth/gmail/callback?code=&state=`** — no auth dependency (Google calls this)
- ALWAYS responds with HTTP 302. Never JSON.
- Error cases (all redirect to `{FRONTEND_URL}{return_to}?gmail_connected=error&reason=<X>`):
  - `?error=` param present → `reason=user_cancelled`
  - `verify_state` raises `StateExpired` → `reason=state_expired`
  - `verify_state` raises `StateInvalid` → `reason=state_invalid`
  - `exchange_code` fails → `reason=exchange_failed`
  - `OAuthTokens.refresh_token` is None/empty → `reason=no_refresh_token`
- Success: `upsert_account(...)`, redirect to `{FRONTEND_URL}{return_to}?gmail_connected=success`
- Duplicate connection (upsert): still success.
- `return_to` defaults to `/settings` if state decode fails after expiry/invalid (redirect to `FRONTEND_URL/settings`).

### `app/routers/accounts.py` (new file)

**`GET /accounts`** — requires `get_current_user`
- Calls `list_user_accounts(user_id)`.
- Returns `list[AccountPublic]`.
- `AccountPublic`: `id, email_address, provider, color, last_synced, disconnected_at` — **no `oauth_token`**.

**`DELETE /accounts/{id}`** — requires `get_current_user`
- `get_account(id)` → 404 if not found.
- If `account.user_id != current_user.user_id` → 404 (don't leak existence).
- `revoke(account.oauth_token.refresh_token)` — swallows failure.
- `delete_account(id)`.
- Returns 204.

Both routers registered in `app/main.py`.

---

## 5. Frontend — `/settings` page

File: `frontend/app/settings/page.tsx` — `"use client"` component.

### On mount
- Read `?gmail_connected` and `?reason` from `useSearchParams()`.
- Show sonner toast:
  - `success` → "Gmail connected successfully"
  - `error&reason=user_cancelled` → "Connection cancelled"
  - `error&reason=state_expired` → "Session expired — please try again"
  - `error&reason=state_invalid` → "Invalid OAuth state — please try again"
  - `error&reason=no_refresh_token` → "No refresh token — revoke Gmail access and reconnect"
  - other error → "Connection failed: {reason}"
- Strip params via `router.replace('/settings')`.

### Connected accounts list
- Fetch `GET /accounts` on mount → render each as a row:
  - Colored dot (inline style with `account.color`)
  - `account.email_address`
  - "Last synced {formatDistanceToNow(account.last_synced)} ago" or "Never synced"
  - **Disconnect** button
- Empty state: "No accounts connected. Click Connect Gmail to get started."

### Connect Gmail
- Button calls `apiFetch<{url: string}>('/auth/gmail/start')` → `window.location.href = url`.

### Disconnect
- Opens shadcn `AlertDialog` ("Are you sure you want to disconnect {email}?").
- On confirm: `apiFetch('/accounts/{id}', {method: 'DELETE'})` → optimistic remove from list.

### Security invariant
After build: `grep -rn "oauth_token\|access_token\|refresh_token" frontend/app frontend/lib frontend/components` must return zero matches in user-visible code.

---

## 6. Tests

### `backend/tests/services/test_gmail_oauth.py`
- `sign_state` / `verify_state` roundtrip — claims preserved
- `verify_state` with expired token → `StateExpired`
- `verify_state` with wrong secret → `StateInvalid`
- `build_authorize_url` contains `client_id`, `redirect_uri`, `response_type=code`, `scope`, `prompt=consent`, `access_type=offline`, `state`
- `exchange_code` happy path — mock token endpoint with `respx`, returns `OAuthTokens`
- `exchange_code` on Google 400 → `OAuthExchangeFailed`
- `refresh_tokens` race — `asyncio.gather` 2 concurrent calls for same `account_id`, `respx` counts requests → assert exactly 1 network call made

### `backend/tests/routers/test_auth_oauth.py`
- `GET /auth/gmail/start` returns JSON with `url` containing `client_id`, `redirect_uri`, `response_type=code`, `prompt=consent`, `state`
- `GET /auth/gmail/callback` with valid code + state → 302 to `FRONTEND_URL/settings?gmail_connected=success`
- `GET /auth/gmail/callback` with expired state → 302 `reason=state_expired`
- `GET /auth/gmail/callback` with bad-signature state → 302 `reason=state_invalid`
- `GET /auth/gmail/callback?error=access_denied` → 302 `reason=user_cancelled`

### `backend/tests/routers/test_accounts.py`
- `GET /accounts` returns only the authenticated user's accounts (not another user's)
- Response shape: `oauth_token` field absent (explicit assertion)
- `DELETE /accounts/{id}` as owner → 204
- `DELETE /accounts/{other_user_account_id}` as user A → 404

---

## Constraints (non-negotiable)

- `/auth/gmail/callback` NEVER returns JSON. Always 302.
- `oauth_token` JSONB column writes are atomic (single UPSERT or UPDATE).
- All datetimes timezone-aware UTC: `datetime.now(timezone.utc)`.
- Frontend never sees `oauth_token`, `access_token`, or `refresh_token`.
- CORS allowlist: deployed frontend URL + `http://localhost:3000`. No wildcards.
- Service role key referenced only in `app/db/supabase.py`.
