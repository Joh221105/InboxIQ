# InboxIQ Foundation (Issue 1A) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete the existing flat backend and non-spec migrations, then build the spec-prescribed full-stack foundation (backend structure, auth, DB helpers, routers, migrations, frontend stubs, Makefile, CI).

**Architecture:** Approach A — delete first, build clean. Backend reorganized into `app/core/`, `app/db/`, `app/models/`, `app/routers/` with placeholder `services/`, `prompts/`, `tasks/`. Frontend existing tree extended with new route pages, `lib/api.ts`, `types/`, and updated middleware. Six idempotent SQL migrations replace the five misnamed existing ones.

**Tech Stack:** FastAPI + Pydantic v2 + supabase-py + PyJWT + httpx (backend); Next.js 14 + TypeScript strict + shadcn/ui + @supabase/ssr (frontend); pytest + pytest-asyncio + respx (backend tests).

---

## File Map

**Delete (before writing anything new):**
- `backend/app/auth_jwt.py`, `config.py`, `gmail_fetch.py`, `gmail_oauth.py`, `main.py`, `oauth_state.py`, `supabase_client.py`
- `backend/app/routers/emails.py`, `backend/app/routers/gmail_auth.py`
- `backend/app/__pycache__/`, `backend/app/routers/__pycache__/`
- `supabase/migrations/001_connected_accounts.sql` through `005_contact_tags.sql`
- `frontend/app/login/` (entire directory)

**Create (backend):**
| File | Responsibility |
|------|---------------|
| `backend/app/__init__.py` | package marker |
| `backend/app/core/__init__.py` | package marker |
| `backend/app/core/config.py` | Pydantic Settings singleton, all env vars |
| `backend/app/core/auth.py` | `verify_jwt`, `UserClaims`, `get_current_user` dep |
| `backend/app/db/__init__.py` | package marker |
| `backend/app/db/supabase.py` | `get_anon_client()`, `get_service_client()` |
| `backend/app/db/users.py` | `get_user()`, `update_default_context()` |
| `backend/app/models/__init__.py` | package marker |
| `backend/app/models/user.py` | `User` Pydantic model |
| `backend/app/routers/__init__.py` | package marker |
| `backend/app/routers/auth.py` | 501 stubs for gmail start/callback |
| `backend/app/routers/users.py` | GET /users/me, PATCH /users/me/context |
| `backend/app/services/__init__.py` | placeholder |
| `backend/app/prompts/__init__.py` | placeholder |
| `backend/app/tasks/__init__.py` | placeholder |
| `backend/app/main.py` | FastAPI app, CORS, lifespan, /health |
| `backend/scripts/print_migrations.py` | prints migrations to stdout |
| `backend/supabase/migrations/001_users.sql` | users table + RLS |
| `backend/supabase/migrations/002_connected_accounts.sql` | accounts table + RLS |
| `backend/supabase/migrations/003_emails.sql` | emails table + RLS |
| `backend/supabase/migrations/004_contact_tags.sql` | contact_tags table + RLS |
| `backend/supabase/migrations/005_auth_trigger.sql` | auto-insert users on signup |
| `backend/supabase/migrations/006_color_palette.sql` | color assignment function |
| `backend/supabase/tests/test_rls.sql` | 8 adversarial RLS queries |
| `backend/tests/__init__.py` | package marker |
| `backend/tests/conftest.py` | env vars + fixtures |
| `backend/tests/core/__init__.py` | package marker |
| `backend/tests/core/test_auth.py` | JWT tests (HS256 + ES256) |
| `backend/tests/routers/__init__.py` | package marker |
| `backend/tests/routers/test_users.py` | users router tests |
| `backend/pytest.ini` | asyncio_mode = auto |
| `backend/.env.example` | all vars with comments |

**Modify (backend):**
| File | Change |
|------|--------|
| `backend/requirements.txt` | pin all packages per spec + add ruff/mypy/respx dev deps |

**Create (frontend):**
| File | Responsibility |
|------|---------------|
| `frontend/app/auth/sign-in/page.tsx` | magic-link form (replaces login/) |
| `frontend/app/inbox/page.tsx` | placeholder stub |
| `frontend/app/packages/page.tsx` | placeholder stub |
| `frontend/app/contacts/page.tsx` | placeholder stub |
| `frontend/app/settings/page.tsx` | placeholder stub |
| `frontend/components/sign-out-button.tsx` | client component for sign-out |
| `frontend/types/index.ts` | shared TS types (User, Email, etc.) |
| `frontend/lib/api.ts` | typed fetch wrapper + ApiError |
| `frontend/.env.example` | all vars with comments |

**Modify (frontend):**
| File | Change |
|------|--------|
| `frontend/app/layout.tsx` | add sidebar nav + sign-out button |
| `frontend/app/page.tsx` | simple "Home" placeholder |
| `frontend/app/auth/callback/route.ts` | fix error redirect to /auth/sign-in |
| `frontend/middleware.ts` | protect 5 routes, redirect to /auth/sign-in |
| `frontend/package.json` | add @tanstack/react-query, date-fns, sonner + vitest/playwright dev deps |

**Create (repo root):**
| File | Responsibility |
|------|---------------|
| `Makefile` | install, dev, test, lint, typecheck, format, migrations |
| `.github/workflows/ci.yml` | PR lint + typecheck + test for both stacks |

**Modify (repo root):**
| File | Change |
|------|--------|
| `README.md` | add Migrations subsection |

---

## Task 1: Delete old files and scaffold folder structure

**Files:**
- Delete: all listed in "Delete" section above
- Create: all `__init__.py` package markers and empty placeholder packages

- [ ] **Step 1: Delete backend flat files and old migrations**

```bash
cd /path/to/repo

# Backend flat app files
rm backend/app/auth_jwt.py backend/app/config.py backend/app/gmail_fetch.py \
   backend/app/gmail_oauth.py backend/app/main.py backend/app/oauth_state.py \
   backend/app/supabase_client.py

# Backend routers
rm backend/app/routers/emails.py backend/app/routers/gmail_auth.py

# Pycache
rm -rf backend/app/__pycache__ backend/app/routers/__pycache__

# Old migrations (supabase/ is at repo root, not in backend/)
rm supabase/migrations/001_connected_accounts.sql \
   supabase/migrations/002_users_profile.sql \
   supabase/migrations/003_account_color_assignment.sql \
   supabase/migrations/004_emails.sql \
   supabase/migrations/005_contact_tags.sql
```

- [ ] **Step 2: Delete frontend login page**

```bash
rm -rf frontend/app/login
```

- [ ] **Step 3: Create new backend folder structure**

```bash
# Core, db, models subdirs
mkdir -p backend/app/core backend/app/db backend/app/models \
          backend/app/services backend/app/prompts backend/app/tasks

# Scripts and test dirs
mkdir -p backend/scripts
mkdir -p backend/tests/core backend/tests/routers
mkdir -p backend/supabase/migrations backend/supabase/tests
```

- [ ] **Step 4: Write all package markers**

Create each of these as an empty file:

```bash
touch backend/app/__init__.py
touch backend/app/core/__init__.py
touch backend/app/db/__init__.py
touch backend/app/models/__init__.py
touch backend/app/routers/__init__.py
touch backend/app/services/__init__.py
touch backend/app/prompts/__init__.py
touch backend/app/tasks/__init__.py
touch backend/tests/__init__.py
touch backend/tests/core/__init__.py
touch backend/tests/routers/__init__.py
```

- [ ] **Step 5: Create frontend dirs**

```bash
mkdir -p frontend/app/inbox frontend/app/packages \
          frontend/app/contacts frontend/app/settings \
          frontend/app/auth/sign-in
mkdir -p frontend/types
```

- [ ] **Step 6: Commit scaffold**

```bash
git add -A
git commit -m "chore(scaffold): delete old backend files, create new folder structure"
```

---

## Task 2: Update requirements.txt

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Rewrite requirements.txt**

```
# backend/requirements.txt
fastapi==0.115.*
uvicorn[standard]==0.32.*
pydantic==2.9.*
pydantic-settings==2.6.*
httpx==0.27.*
supabase==2.9.*
google-api-python-client==2.149.*
google-auth-oauthlib==1.2.*
openai==1.54.*
apscheduler==3.10.*
tenacity==9.0.*
PyJWT[crypto]==2.9.*
beautifulsoup4==4.12.*

# dev
pytest==8.3.*
pytest-asyncio==0.24.*
respx==0.21.*
ruff>=0.4.0
mypy>=1.10.0
```

- [ ] **Step 2: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore(deps): pin backend requirements per spec"
```

---

## Task 3: pytest.ini + tests/conftest.py

**Files:**
- Create: `backend/pytest.ini`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write pytest.ini**

```ini
# backend/pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 2: Write conftest.py**

Set env vars at module level before any app imports so the `settings` singleton is created with test values.

```python
# backend/tests/conftest.py
from __future__ import annotations

import os

# Must be set before any app module is imported
os.environ.update(
    {
        "SUPABASE_URL": "https://testproject.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key-long-enough-here",
        "SUPABASE_ANON_KEY": "test-anon-key",
        "SUPABASE_JWT_SECRET": "super-secret-test-jwt-secret-at-least-32-chars!",
        "GMAIL_CLIENT_ID": "test-gmail-client-id.apps.googleusercontent.com",
        "GMAIL_CLIENT_SECRET": "test-gmail-client-secret",
        "GMAIL_REDIRECT_URI": "http://localhost:8000/auth/gmail/callback",
        "OAUTH_STATE_SECRET": "test-oauth-state-secret-at-least-32-chars!",
        "OPENAI_API_KEY": "sk-test-openai-key",
        "FRONTEND_URL": "http://localhost:3000",
    }
)

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
```

- [ ] **Step 3: Commit**

```bash
git add backend/pytest.ini backend/tests/conftest.py
git commit -m "test(setup): add pytest config and conftest with test env vars"
```

---

## Task 4: Write failing auth tests

**Files:**
- Create: `backend/tests/core/test_auth.py`

Write the tests now — they will fail until `app/core/auth.py` is implemented.

- [ ] **Step 1: Write test_auth.py**

```python
# backend/tests/core/test_auth.py
from __future__ import annotations

import json
import time
from uuid import uuid4

import httpx
import jwt
import pytest
import respx
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import HTTPException
from jwt.algorithms import ECAlgorithm

from app.core import auth as auth_module
from app.core.auth import UserClaims, verify_jwt

_SECRET = "super-secret-test-jwt-secret-at-least-32-chars!"
_USER_ID = str(uuid4())
_EMAIL = "test@example.com"
_SUPABASE_URL = "https://testproject.supabase.co"


def _hs256_token(
    user_id: str = _USER_ID,
    email: str = _EMAIL,
    expired: bool = False,
    omit_sub: bool = False,
) -> str:
    now = int(time.time())
    payload: dict = {
        "aud": "authenticated",
        "iat": now - 10,
        "exp": (now - 60) if expired else (now + 3600),
        "email": email,
    }
    if not omit_sub:
        payload["sub"] = user_id
    return jwt.encode(payload, _SECRET, algorithm="HS256")


async def test_hs256_happy_path() -> None:
    token = _hs256_token()
    claims = await verify_jwt(token)
    assert isinstance(claims, UserClaims)
    assert str(claims.user_id) == _USER_ID
    assert claims.email == _EMAIL


async def test_hs256_expired_raises_auth_expired() -> None:
    token = _hs256_token(expired=True)
    with pytest.raises(HTTPException) as exc:
        await verify_jwt(token)
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "auth_expired"


async def test_hs256_mangled_raises_auth_invalid() -> None:
    with pytest.raises(HTTPException) as exc:
        await verify_jwt("this.is.garbage")
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "auth_invalid"


async def test_hs256_missing_sub_raises_auth_invalid() -> None:
    token = _hs256_token(omit_sub=True)
    with pytest.raises(HTTPException) as exc:
        await verify_jwt(token)
    assert exc.value.status_code == 401
    assert exc.value.detail["code"] == "auth_invalid"


async def test_es256_with_mocked_jwks() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    kid = "test-ec-key-id"
    now = int(time.time())
    payload = {
        "aud": "authenticated",
        "sub": _USER_ID,
        "email": _EMAIL,
        "iat": now - 10,
        "exp": now + 3600,
    }
    token = jwt.encode(
        payload, private_key, algorithm="ES256", headers={"kid": kid}
    )

    pub_jwk = json.loads(ECAlgorithm.to_jwk(private_key.public_key()))
    pub_jwk.update({"kid": kid, "alg": "ES256", "use": "sig"})
    jwks_payload = {"keys": [pub_jwk]}

    # Clear JWKS cache so the mock is actually called
    auth_module._jwks_cache.clear()

    jwks_url = f"{_SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    with respx.mock:
        respx.get(jwks_url).mock(
            return_value=httpx.Response(200, json=jwks_payload)
        )
        claims = await verify_jwt(token)

    assert str(claims.user_id) == _USER_ID
    assert claims.email == _EMAIL
```

- [ ] **Step 2: Run tests — confirm they fail with ImportError**

Run from `backend/` directory (with venv activated):

```bash
cd backend
python -m pytest tests/core/test_auth.py -v 2>&1 | head -30
```

Expected: `ImportError` or `ModuleNotFoundError` for `app.core.auth`.

- [ ] **Step 3: Commit failing tests**

```bash
git add backend/tests/core/test_auth.py
git commit -m "test(auth): write failing JWT verification tests"
```

---

## Task 5: app/core/config.py

**Files:**
- Create: `backend/app/core/config.py`

- [ ] **Step 1: Write config.py**

```python
# backend/app/core/config.py
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Required
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str
    supabase_jwt_secret: str = ""  # empty = Supabase JWKS (ES256/RS256)
    gmail_client_id: str
    gmail_client_secret: str
    gmail_redirect_uri: str
    oauth_state_secret: str
    openai_api_key: str
    frontend_url: str

    # Optional with defaults
    environment: str = "dev"
    log_level: str = "INFO"
    allowed_origins: str = ""  # comma-separated; empty → derive from frontend_url
    token_encryption_key: str | None = None
    sentry_dsn: str | None = None
    git_sha: str = "dev"

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins:
            return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        return list({self.frontend_url.rstrip("/"), "http://localhost:3000"})


settings = Settings()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/core/config.py
git commit -m "feat(config): add Pydantic Settings singleton with all env vars"
```

---

## Task 6: app/models/user.py and app/db/supabase.py

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/db/supabase.py`

- [ ] **Step 1: Write user.py**

```python
# backend/app/models/user.py
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: UUID
    email: str
    default_context: str
    created_at: datetime
```

- [ ] **Step 2: Write supabase.py**

```python
# backend/app/db/supabase.py
"""Two clients:
- get_anon_client(): respects RLS. Use sparingly on the backend; mostly for tests.
- get_service_client(): bypasses RLS. Use for backend operations on behalf of a
  verified user. NEVER expose to the frontend.
"""
from __future__ import annotations

from supabase import Client, create_client

from app.core.config import settings


def get_anon_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_service_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/user.py backend/app/db/supabase.py
git commit -m "feat(models,db): add User model and Supabase client factory"
```

---

## Task 7: app/core/auth.py — implement and pass auth tests

**Files:**
- Create: `backend/app/core/auth.py`

- [ ] **Step 1: Write auth.py**

```python
# backend/app/core/auth.py
from __future__ import annotations

import time
from typing import Any
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import settings

# Module-level JWKS cache: {"keys": [...], "expires_at": float}
_jwks_cache: dict[str, Any] = {}

_bearer = HTTPBearer(auto_error=False)


class UserClaims(BaseModel):
    user_id: UUID
    email: str


def _invalid(msg: str = "Invalid token") -> HTTPException:
    return HTTPException(
        status_code=401, detail={"code": "auth_invalid", "message": msg}
    )


def _expired() -> HTTPException:
    return HTTPException(
        status_code=401, detail={"code": "auth_expired", "message": "Token expired"}
    )


async def _fetch_jwks() -> list[dict[str, Any]]:
    now = time.monotonic()
    if _jwks_cache.get("expires_at", 0.0) > now:
        return _jwks_cache["keys"]  # type: ignore[return-value]
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    _jwks_cache["keys"] = data["keys"]
    _jwks_cache["expires_at"] = now + 300.0
    return data["keys"]  # type: ignore[return-value]


async def verify_jwt(token: str) -> UserClaims:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise _invalid()

    alg = header.get("alg", "HS256")

    try:
        if alg in ("ES256", "RS256"):
            keys = await _fetch_jwks()
            kid = header.get("kid")
            from jwt import PyJWKSet  # noqa: PLC0415

            jwk_set = PyJWKSet.from_dict({"keys": keys})
            signing_key = None
            for k in jwk_set.keys:
                if kid is None or k.key_id == kid:
                    signing_key = k.key
                    break
            if signing_key is None:
                raise _invalid("No matching JWKS key")
            payload = jwt.decode(
                token, signing_key, algorithms=[alg], audience="authenticated"
            )
        else:
            if not settings.supabase_jwt_secret:
                raise _invalid("HS256 not configured")
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
    except jwt.ExpiredSignatureError:
        raise _expired()
    except HTTPException:
        raise
    except jwt.PyJWTError:
        raise _invalid()

    sub = payload.get("sub")
    if not sub:
        raise _invalid("Missing sub claim")

    try:
        return UserClaims(user_id=UUID(str(sub)), email=payload.get("email", ""))
    except (ValueError, TypeError):
        raise _invalid("Invalid sub UUID")


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> UserClaims:
    if not creds or creds.scheme.lower() != "bearer":
        raise _invalid("Missing bearer token")
    return await verify_jwt(creds.credentials)
```

- [ ] **Step 2: Install deps and run auth tests — all must pass**

```bash
cd backend
pip install -r requirements.txt
python -m pytest tests/core/test_auth.py -v
```

Expected output:
```
PASSED tests/core/test_auth.py::test_hs256_happy_path
PASSED tests/core/test_auth.py::test_hs256_expired_raises_auth_expired
PASSED tests/core/test_auth.py::test_hs256_mangled_raises_auth_invalid
PASSED tests/core/test_auth.py::test_hs256_missing_sub_raises_auth_invalid
PASSED tests/core/test_auth.py::test_es256_with_mocked_jwks
5 passed
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/auth.py
git commit -m "feat(auth): add JWT verification with HS256/ES256 and JWKS caching"
```

---

## Task 8: Write failing users router tests

**Files:**
- Create: `backend/tests/routers/test_users.py`

- [ ] **Step 1: Write test_users.py**

```python
# backend/tests/routers/test_users.py
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.user import User

_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
_EMAIL = "test@example.com"
_USER = User(
    id=_USER_ID,
    email=_EMAIL,
    default_context="Daily",
    created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
)


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email=_EMAIL)


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client() -> TestClient:
    with TestClient(app) as c:
        yield c


# --- GET /users/me ---


def test_get_me_happy(authed_client: TestClient) -> None:
    with patch("app.routers.users.get_user", new=AsyncMock(return_value=_USER)):
        resp = authed_client.get("/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == _EMAIL
    assert data["default_context"] == "Daily"


def test_get_me_no_token(unauthed_client: TestClient) -> None:
    resp = unauthed_client.get("/users/me")
    assert resp.status_code == 401


def test_get_me_mangled_token(unauthed_client: TestClient) -> None:
    resp = unauthed_client.get(
        "/users/me", headers={"Authorization": "Bearer not.a.real.token"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"]["code"] == "auth_invalid"


# --- PATCH /users/me/context ---


def test_patch_context_happy(authed_client: TestClient) -> None:
    updated = _USER.model_copy(update={"default_context": "Job Hunting"})
    with patch(
        "app.routers.users.update_default_context",
        new=AsyncMock(return_value=updated),
    ):
        resp = authed_client.patch(
            "/users/me/context", json={"context": "Job Hunting"}
        )
    assert resp.status_code == 200
    assert resp.json()["default_context"] == "Job Hunting"


def test_patch_context_invalid_value(authed_client: TestClient) -> None:
    resp = authed_client.patch(
        "/users/me/context", json={"context": "Invalid Context"}
    )
    assert resp.status_code == 422
```

- [ ] **Step 2: Run — confirm ImportError (routers not yet created)**

```bash
cd backend
python -m pytest tests/routers/test_users.py -v 2>&1 | head -20
```

Expected: `ImportError` for `app.main` or `app.routers.users`.

- [ ] **Step 3: Commit failing tests**

```bash
git add backend/tests/routers/test_users.py
git commit -m "test(users): write failing users router tests"
```

---

## Task 9: app/db/users.py

**Files:**
- Create: `backend/app/db/users.py`

- [ ] **Step 1: Write users.py**

```python
# backend/app/db/users.py
from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import HTTPException

from app.db.supabase import get_service_client
from app.models.user import User


async def get_user(user_id: UUID) -> User:
    def _fetch() -> dict | None:
        result = (
            get_service_client()
            .table("users")
            .select("*")
            .eq("id", str(user_id))
            .maybe_single()
            .execute()
        )
        return result.data  # type: ignore[return-value]

    data = await asyncio.to_thread(_fetch)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**data)


async def update_default_context(user_id: UUID, context: str) -> User:
    def _update() -> dict | None:
        result = (
            get_service_client()
            .table("users")
            .update({"default_context": context})
            .eq("id", str(user_id))
            .execute()
        )
        rows = result.data or []
        return rows[0] if rows else None

    data = await asyncio.to_thread(_update)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**data)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/db/users.py
git commit -m "feat(db): add get_user and update_default_context helpers"
```

---

## Task 10: app/routers/auth.py (stubs) and app/routers/users.py

**Files:**
- Create: `backend/app/routers/auth.py`
- Create: `backend/app/routers/users.py`

- [ ] **Step 1: Write auth.py stubs**

```python
# backend/app/routers/auth.py
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth/gmail", tags=["gmail-auth"])


@router.get("/start")
async def gmail_oauth_start() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"detail": "Not implemented — see Issue 1B"},
    )


@router.get("/callback")
async def gmail_oauth_callback() -> JSONResponse:
    return JSONResponse(
        status_code=501,
        content={"detail": "Not implemented — see Issue 1B"},
    )
```

- [ ] **Step 2: Write users.py router**

```python
# backend/app/routers/users.py
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import UserClaims, get_current_user
from app.db.users import get_user, update_default_context
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

ContextValue = Literal[
    "Job Hunting", "Shopping", "School Application", "Daily"
]


class UpdateContextBody(BaseModel):
    context: ContextValue


@router.get("/me")
async def get_me(claims: UserClaims = Depends(get_current_user)) -> User:
    return await get_user(claims.user_id)


@router.patch("/me/context")
async def patch_context(
    body: UpdateContextBody,
    claims: UserClaims = Depends(get_current_user),
) -> User:
    return await update_default_context(claims.user_id, body.context)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/auth.py backend/app/routers/users.py
git commit -m "feat(routers): add 501 auth stubs and users router"
```

---

## Task 11: app/main.py

**Files:**
- Create: `backend/app/main.py`

- [ ] **Step 1: Write main.py**

```python
# backend/app/main.py
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, users

logger = logging.getLogger(__name__)

_REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_ANON_KEY",
    "GMAIL_CLIENT_ID",
    "GMAIL_CLIENT_SECRET",
    "GMAIL_REDIRECT_URI",
    "OAUTH_STATE_SECRET",
    "OPENAI_API_KEY",
    "FRONTEND_URL",
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    for var in _REQUIRED_ENV_VARS:
        logger.info("env %s present=%s", var, bool(os.getenv(var)))
    yield


app = FastAPI(title="InboxIQ API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)


async def _probe_supabase() -> str:
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(
                f"{settings.supabase_url.rstrip('/')}/auth/v1/health"
            )
            return "ok" if resp.status_code == 200 else "down"
    except Exception:
        return "down"


async def _probe_openai() -> str:
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            )
            return "ok" if resp.status_code == 200 else "down"
    except Exception:
        return "down"


@app.get("/health")
async def health() -> dict:
    supabase_status, openai_status = await asyncio.gather(
        _probe_supabase(), _probe_openai()
    )
    return {
        "status": "ok",
        "version": settings.git_sha,
        "deps": {"supabase": supabase_status, "openai": openai_status},
    }
```

- [ ] **Step 2: Run ALL backend tests — all must pass**

```bash
cd backend
python -m pytest tests/ -v
```

Expected:
```
PASSED tests/core/test_auth.py::test_hs256_happy_path
PASSED tests/core/test_auth.py::test_hs256_expired_raises_auth_expired
PASSED tests/core/test_auth.py::test_hs256_mangled_raises_auth_invalid
PASSED tests/core/test_auth.py::test_hs256_missing_sub_raises_auth_invalid
PASSED tests/core/test_auth.py::test_es256_with_mocked_jwks
PASSED tests/routers/test_users.py::test_get_me_happy
PASSED tests/routers/test_users.py::test_get_me_no_token
PASSED tests/routers/test_users.py::test_get_me_mangled_token
PASSED tests/routers/test_users.py::test_patch_context_happy
PASSED tests/routers/test_users.py::test_patch_context_invalid_value
10 passed
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat(main): add FastAPI app with CORS, lifespan logging, and /health"
```

---

## Task 12: Migrations 001–006

**Files:**
- Create: `backend/supabase/migrations/001_users.sql` through `006_color_palette.sql`

Note: these live under `backend/supabase/migrations/` (not `supabase/migrations/` at repo root). The repo-root `supabase/migrations/` was cleared in Task 1. The spec's migration runner reads from `backend/supabase/migrations/`.

- [ ] **Step 1: Write 001_users.sql**

```sql
-- backend/supabase/migrations/001_users.sql
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    default_context TEXT NOT NULL DEFAULT 'Daily'
        CHECK (default_context IN ('Job Hunting', 'Shopping', 'School Application', 'Daily')),
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public'
      AND tablename = 'users' AND policyname = 'users_self_select'
  ) THEN
    CREATE POLICY "users_self_select" ON public.users
      FOR SELECT USING (id = auth.uid());
  END IF;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public'
      AND tablename = 'users' AND policyname = 'users_self_update'
  ) THEN
    CREATE POLICY "users_self_update" ON public.users
      FOR UPDATE USING (id = auth.uid());
  END IF;
END $$;
```

- [ ] **Step 2: Write 002_connected_accounts.sql**

```sql
-- backend/supabase/migrations/002_connected_accounts.sql
CREATE TABLE IF NOT EXISTS public.connected_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    email_address TEXT NOT NULL,
    provider TEXT NOT NULL CHECK (provider IN ('gmail', 'outlook')),
    oauth_token JSONB NOT NULL,
    color TEXT NOT NULL,
    last_synced TIMESTAMPTZ,
    disconnected_at TIMESTAMPTZ,
    disconnected_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, email_address)
);

CREATE INDEX IF NOT EXISTS idx_accounts_user
    ON public.connected_accounts(user_id);

ALTER TABLE public.connected_accounts ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public'
      AND tablename = 'connected_accounts' AND policyname = 'accounts_user_all'
  ) THEN
    CREATE POLICY "accounts_user_all" ON public.connected_accounts
      FOR ALL USING (user_id = auth.uid())
      WITH CHECK (user_id = auth.uid());
  END IF;
END $$;
```

- [ ] **Step 3: Write 003_emails.sql**

```sql
-- backend/supabase/migrations/003_emails.sql
CREATE TABLE IF NOT EXISTS public.emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES public.connected_accounts(id) ON DELETE CASCADE,
    external_id TEXT NOT NULL,
    sender_email TEXT NOT NULL DEFAULT '',
    subject TEXT DEFAULT '',
    body_preview TEXT DEFAULT '',
    received_at TIMESTAMPTZ NOT NULL,
    ai_summary TEXT,
    triage_category TEXT CHECK (triage_category IN
        ('action_required', 'worth_reading', 'auto_archive')),
    triage_context TEXT,
    deadline_extracted DATE,
    action_items JSONB,
    is_pickup_code BOOLEAN DEFAULT false,
    pickup_code TEXT,
    pickup_expiry DATE,
    pickup_used BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    ai_processed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(account_id, external_id)
);

CREATE INDEX IF NOT EXISTS idx_emails_account_received
    ON public.emails(account_id, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_emails_triage
    ON public.emails(triage_category, is_archived);
CREATE INDEX IF NOT EXISTS idx_emails_pickup
    ON public.emails(is_pickup_code, pickup_used)
    WHERE is_pickup_code = true;
CREATE INDEX IF NOT EXISTS idx_emails_unprocessed
    ON public.emails(ai_processed)
    WHERE ai_processed = false;

ALTER TABLE public.emails ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public'
      AND tablename = 'emails' AND policyname = 'emails_via_account'
  ) THEN
    CREATE POLICY "emails_via_account" ON public.emails
      FOR ALL USING (
        account_id IN (
          SELECT id FROM public.connected_accounts WHERE user_id = auth.uid()
        )
      )
      WITH CHECK (
        account_id IN (
          SELECT id FROM public.connected_accounts WHERE user_id = auth.uid()
        )
      );
  END IF;
END $$;
```

- [ ] **Step 4: Write 004_contact_tags.sql**

```sql
-- backend/supabase/migrations/004_contact_tags.sql
CREATE TABLE IF NOT EXISTS public.contact_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    identifier TEXT NOT NULL,
    tag TEXT NOT NULL CHECK (tag IN ('professor', 'friend', 'recruiter', 'custom')),
    custom_label TEXT,
    color TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, identifier)
);

CREATE INDEX IF NOT EXISTS idx_contact_tags_user
    ON public.contact_tags(user_id);

ALTER TABLE public.contact_tags ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE schemaname = 'public'
      AND tablename = 'contact_tags' AND policyname = 'tags_user_all'
  ) THEN
    CREATE POLICY "tags_user_all" ON public.contact_tags
      FOR ALL USING (user_id = auth.uid())
      WITH CHECK (user_id = auth.uid());
  END IF;
END $$;
```

- [ ] **Step 5: Write 005_auth_trigger.sql**

```sql
-- backend/supabase/migrations/005_auth_trigger.sql
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO public.users (id, email)
    VALUES (NEW.id, NEW.email)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();
```

- [ ] **Step 6: Write 006_color_palette.sql**

```sql
-- backend/supabase/migrations/006_color_palette.sql
CREATE OR REPLACE FUNCTION public.next_account_color(p_user_id UUID)
RETURNS TEXT LANGUAGE plpgsql AS $$
DECLARE
    palette TEXT[] := ARRAY[
        '#3B82F6', '#10B981', '#F59E0B', '#EF4444',
        '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'
    ];
    n INT;
BEGIN
    SELECT COUNT(*) INTO n
    FROM public.connected_accounts
    WHERE user_id = p_user_id;
    RETURN palette[(n % 8) + 1];
END $$;
```

- [ ] **Step 7: Commit all migrations**

```bash
git add backend/supabase/migrations/
git commit -m "feat(migrations): add 6 idempotent SQL migrations with RLS policies"
```

---

## Task 13: supabase/tests/test_rls.sql

**Files:**
- Create: `backend/supabase/tests/test_rls.sql`

- [ ] **Step 1: Write test_rls.sql**

```sql
-- backend/supabase/tests/test_rls.sql
-- Adversarial RLS tests. Run as user A against user B's data.
-- Every query MUST return 0 rows. Run in Supabase SQL Editor after
-- setting the JWT claim for user A:
--   SET request.jwt.claims = '{"sub": "<user_a_id>", "role": "authenticated"}';

-- Setup: replace these UUIDs before running
-- :user_b_id        = UUID of user B
-- :user_b_account   = UUID of user B's connected_account
-- :user_b_email     = UUID of user B's email row
-- :user_b_tag       = UUID of user B's contact_tag
-- :user_b_account_id (same as user_b_account)

-- 1. Read user B's emails directly
SELECT * FROM public.emails
WHERE account_id = :'user_b_account';
-- Expected: 0 rows

-- 2. Read user B's connected accounts directly
SELECT * FROM public.connected_accounts
WHERE user_id = :'user_b_id';
-- Expected: 0 rows

-- 3. Insert email tied to user B's account_id — should fail with RLS violation
INSERT INTO public.emails (account_id, external_id, received_at)
VALUES (:'user_b_account', 'injected-001', now());
-- Expected: RLS policy violation error

-- 4. Update user B's email is_archived
UPDATE public.emails SET is_archived = true
WHERE id = :'user_b_email';
-- Expected: 0 rows updated

-- 5. Delete user B's contact_tag
DELETE FROM public.contact_tags
WHERE id = :'user_b_tag';
-- Expected: 0 rows deleted

-- 6. Read user B's users row
SELECT * FROM public.users
WHERE id = :'user_b_id';
-- Expected: 0 rows

-- 7. Insert contact_tag with user_id = user B — should fail
INSERT INTO public.contact_tags (user_id, identifier, tag, color)
VALUES (:'user_b_id', 'injected@example.com', 'custom', '#000000');
-- Expected: RLS policy violation error

-- 8. Update user B's connected_account oauth_token
UPDATE public.connected_accounts
SET oauth_token = '{"stolen": true}'::jsonb
WHERE id = :'user_b_account';
-- Expected: 0 rows updated
```

- [ ] **Step 2: Commit**

```bash
git add backend/supabase/tests/test_rls.sql
git commit -m "test(rls): add 8 adversarial RLS queries for cross-user isolation"
```

---

## Task 14: backend/scripts/print_migrations.py

**Files:**
- Create: `backend/scripts/print_migrations.py`

- [ ] **Step 1: Write print_migrations.py**

```python
# backend/scripts/print_migrations.py
from __future__ import annotations

import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent.parent / "supabase" / "migrations"


def main() -> None:
    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        print("No migration files found in", MIGRATIONS_DIR, file=sys.stderr)
        sys.exit(1)
    for path in sql_files:
        print(f"-- ===== {path.name} =====")
        print(path.read_text(encoding="utf-8"))
        print()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify it runs and prints all 6 files**

```bash
cd backend
python scripts/print_migrations.py | grep "====="
```

Expected:
```
-- ===== 001_users.sql =====
-- ===== 002_connected_accounts.sql =====
-- ===== 003_emails.sql =====
-- ===== 004_contact_tags.sql =====
-- ===== 005_auth_trigger.sql =====
-- ===== 006_color_palette.sql =====
```

- [ ] **Step 3: Commit**

```bash
git add backend/scripts/print_migrations.py
git commit -m "feat(scripts): add migration printer for Supabase SQL editor"
```

---

## Task 15: backend/.env.example

**Files:**
- Create: `backend/.env.example`

- [ ] **Step 1: Write .env.example**

```bash
# backend/.env.example

# Supabase project URL (from Settings → API)
SUPABASE_URL=https://yourproject.supabase.co

# Service role key — backend only, NEVER expose to frontend (Settings → API)
SUPABASE_SERVICE_ROLE_KEY=

# Anon/public key — safe for frontend use (Settings → API)
SUPABASE_ANON_KEY=

# JWT secret for legacy HS256 tokens (Settings → API → JWT Settings)
# Leave empty if your project uses "JWT Signing Keys" (ES256/RS256 via JWKS)
SUPABASE_JWT_SECRET=

# Gmail OAuth credentials from Google Cloud Console
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
# Must exactly match an Authorized Redirect URI in Google Cloud Console
GMAIL_REDIRECT_URI=http://localhost:8000/auth/gmail/callback

# Random secret used to sign OAuth state parameters (prevent CSRF)
OAUTH_STATE_SECRET=

# OpenAI API key (required for AI triage — issues 4+)
OPENAI_API_KEY=

# Frontend URL for CORS allowlist and OAuth redirects
FRONTEND_URL=http://localhost:3000

# Optional: override comma-separated CORS origins (defaults to FRONTEND_URL + localhost:3000)
# ALLOWED_ORIGINS=https://yourapp.vercel.app,http://localhost:3000

# Optional: "dev" or "production"
# ENVIRONMENT=dev

# Optional: log level (DEBUG, INFO, WARNING, ERROR)
# LOG_LEVEL=INFO

# Optional: Fernet key for encrypting stored OAuth tokens at rest
# TOKEN_ENCRYPTION_KEY=

# Optional: Sentry DSN for error tracking
# SENTRY_DSN=

# Set automatically by Railway/CI — current git SHA for /health version field
# GIT_SHA=dev
```

- [ ] **Step 2: Commit**

```bash
git add backend/.env.example
git commit -m "chore(env): add backend .env.example with all vars documented"
```

---

## Task 16: Frontend — update package.json and install

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 1: Add missing dependencies**

Open `frontend/package.json` and add to `dependencies`:
```json
"@tanstack/react-query": "^5.0.0",
"date-fns": "^3.0.0",
"sonner": "^1.0.0"
```

Add to `devDependencies`:
```json
"vitest": "^1.0.0",
"@vitejs/plugin-react": "^4.0.0",
"@testing-library/react": "^14.0.0",
"@testing-library/jest-dom": "^6.0.0",
"@playwright/test": "^1.40.0",
"concurrently": "^8.0.0"
```

Also add a `"test"` script to `scripts`:
```json
"test": "vitest run"
```

- [ ] **Step 2: Install**

```bash
cd frontend
npm install
```

- [ ] **Step 3: Commit**

```bash
git add frontend/package.json frontend/package-lock.json
git commit -m "chore(deps): add react-query, date-fns, sonner, vitest, playwright"
```

---

## Task 17: Frontend — auth/sign-in page (replace login/)

**Files:**
- Create: `frontend/app/auth/sign-in/page.tsx`

The existing `frontend/app/login/page.tsx` was deleted in Task 1. Recreate as `auth/sign-in/` with one change: the `emailRedirectTo` URL stays at `/auth/callback` (no change needed there).

- [ ] **Step 1: Write auth/sign-in/page.tsx**

```tsx
// frontend/app/auth/sign-in/page.tsx
"use client";

import { useState } from "react";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">(
    "idle"
  );
  const [message, setMessage] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("sending");
    setMessage("");
    try {
      const supabase = createBrowserSupabaseClient();
      const origin = window.location.origin;
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: `${origin}/auth/callback` },
      });
      if (error) {
        setStatus("error");
        setMessage(error.message);
        return;
      }
      setStatus("sent");
      setMessage("Check your email for the sign-in link.");
    } catch {
      setStatus("error");
      setMessage("Something went wrong.");
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-muted/30">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in to InboxIQ</CardTitle>
          <CardDescription>
            We&apos;ll email you a magic link — no password needed.
          </CardDescription>
        </CardHeader>
        <form onSubmit={onSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </div>
            {message && (
              <p
                className={
                  status === "error"
                    ? "text-sm text-destructive"
                    : "text-sm text-muted-foreground"
                }
              >
                {message}
              </p>
            )}
          </CardContent>
          <CardFooter>
            <Button
              type="submit"
              disabled={status === "sending" || status === "sent"}
            >
              {status === "sending" ? "Sending…" : "Send magic link"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Fix auth/callback error redirect**

The existing `frontend/app/auth/callback/route.ts` redirects errors to `/login?error=auth`. Update it to redirect to `/auth/sign-in`:

```typescript
// frontend/app/auth/callback/route.ts
import { NextResponse } from "next/server";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/";

  if (code) {
    const supabase = createServerSupabaseClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(`${origin}/auth/sign-in?error=auth`);
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/auth/sign-in/page.tsx frontend/app/auth/callback/route.ts
git commit -m "feat(frontend): add auth/sign-in page, fix callback error redirect"
```

---

## Task 18: Frontend — route stubs

**Files:**
- Update: `frontend/app/page.tsx`
- Create: `frontend/app/inbox/page.tsx`
- Create: `frontend/app/packages/page.tsx`
- Create: `frontend/app/contacts/page.tsx`
- Create: `frontend/app/settings/page.tsx`

- [ ] **Step 1: Write all stubs**

`frontend/app/page.tsx`:
```tsx
export default function HomePage() {
  return <div className="p-8 text-2xl font-semibold">Home</div>;
}
```

`frontend/app/inbox/page.tsx`:
```tsx
export default function InboxPage() {
  return <div className="p-8 text-2xl font-semibold">Inbox</div>;
}
```

`frontend/app/packages/page.tsx`:
```tsx
export default function PackagesPage() {
  return <div className="p-8 text-2xl font-semibold">Packages</div>;
}
```

`frontend/app/contacts/page.tsx`:
```tsx
export default function ContactsPage() {
  return <div className="p-8 text-2xl font-semibold">Contacts</div>;
}
```

`frontend/app/settings/page.tsx`:
```tsx
export default function SettingsPage() {
  return <div className="p-8 text-2xl font-semibold">Settings</div>;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/app/page.tsx frontend/app/inbox/ frontend/app/packages/ \
         frontend/app/contacts/ frontend/app/settings/
git commit -m "feat(frontend): add placeholder pages for all 5 routes"
```

---

## Task 19: Frontend — layout.tsx + sign-out-button.tsx

**Files:**
- Modify: `frontend/app/layout.tsx`
- Create: `frontend/components/sign-out-button.tsx`

- [ ] **Step 1: Write sign-out-button.tsx**

```tsx
// frontend/components/sign-out-button.tsx
"use client";

import { useRouter } from "next/navigation";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

export default function SignOutButton() {
  const router = useRouter();

  async function handleSignOut() {
    const supabase = createBrowserSupabaseClient();
    await supabase.auth.signOut();
    router.push("/auth/sign-in");
  }

  return (
    <Button
      variant="ghost"
      className="w-full justify-start text-muted-foreground"
      onClick={handleSignOut}
    >
      Sign out
    </Button>
  );
}
```

- [ ] **Step 2: Update layout.tsx**

```tsx
// frontend/app/layout.tsx
import type { Metadata } from "next";
import localFont from "next/font/local";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import Link from "next/link";
import SignOutButton from "@/components/sign-out-button";

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
  description: "AI-powered unified email management",
};

const NAV = [
  { href: "/", label: "Home" },
  { href: "/inbox", label: "Inbox" },
  { href: "/packages", label: "Packages" },
  { href: "/contacts", label: "Contacts" },
  { href: "/settings", label: "Settings" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={cn("font-sans", inter.variable)}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased flex min-h-screen`}
      >
        <nav className="w-56 shrink-0 border-r flex flex-col gap-1 p-4">
          <span className="px-3 py-2 text-sm font-semibold text-foreground mb-2">
            InboxIQ
          </span>
          {NAV.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className="rounded px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            >
              {label}
            </Link>
          ))}
          <div className="mt-auto">
            <SignOutButton />
          </div>
        </nav>
        <main className="flex-1 overflow-auto">{children}</main>
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/app/layout.tsx frontend/components/sign-out-button.tsx
git commit -m "feat(frontend): add sidebar nav with 5 routes and sign-out button"
```

---

## Task 20: Frontend — types/index.ts and lib/api.ts

**Files:**
- Create: `frontend/types/index.ts`
- Create: `frontend/lib/api.ts`

- [ ] **Step 1: Write types/index.ts**

```typescript
// frontend/types/index.ts
export interface User {
  id: string;
  email: string;
  default_context:
    | "Job Hunting"
    | "Shopping"
    | "School Application"
    | "Daily";
  created_at: string;
}

export type TriageCategory =
  | "action_required"
  | "worth_reading"
  | "auto_archive";

export interface Email {
  id: string;
  account_id: string;
  external_id: string;
  sender_email: string;
  subject: string;
  body_preview: string;
  received_at: string;
  ai_summary: string | null;
  triage_category: TriageCategory | null;
  triage_context: string | null;
  deadline_extracted: string | null;
  action_items: unknown[] | null;
  is_pickup_code: boolean;
  pickup_code: string | null;
  pickup_expiry: string | null;
  pickup_used: boolean;
  is_archived: boolean;
  ai_processed: boolean;
  created_at: string;
}

export interface ConnectedAccount {
  id: string;
  user_id: string;
  email_address: string;
  provider: "gmail" | "outlook";
  color: string;
  last_synced: string | null;
  created_at: string;
}

export interface ContactTag {
  id: string;
  user_id: string;
  identifier: string;
  tag: "professor" | "friend" | "recruiter" | "custom";
  custom_label: string | null;
  color: string;
  created_at: string;
}
```

- [ ] **Step 2: Write lib/api.ts**

```typescript
// frontend/lib/api.ts
import { createBrowserSupabaseClient } from "@/lib/supabase/client";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function getAuthToken(): Promise<string | null> {
  const supabase = createBrowserSupabaseClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let code = "unknown_error";
    let message = response.statusText;
    try {
      const body = await response.json();
      code =
        (body?.detail as { code?: string })?.code ??
        (body?.code as string) ??
        code;
      message =
        (body?.detail as { message?: string })?.message ??
        (body?.message as string) ??
        message;
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(response.status, code, message);
  }

  return response.json() as Promise<T>;
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/types/index.ts frontend/lib/api.ts
git commit -m "feat(frontend): add shared TS types and typed API fetch wrapper"
```

---

## Task 21: Frontend — middleware.ts update

**Files:**
- Modify: `frontend/middleware.ts`

Replace the existing middleware (which only refreshes the session) with one that also enforces auth on the five protected routes.

- [ ] **Step 1: Rewrite middleware.ts**

```typescript
// frontend/middleware.ts
import { createServerClient } from "@supabase/ssr";
import { type NextRequest, NextResponse } from "next/server";

const PROTECTED = new Set(["/", "/inbox", "/packages", "/contacts", "/settings"]);

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request });

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return response;

  const supabase = createServerClient(url, key, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) =>
          request.cookies.set(name, value),
        );
        response = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options),
        );
      },
    },
  });

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;
  const isProtected =
    PROTECTED.has(pathname) ||
    [...PROTECTED].some((r) => r !== "/" && pathname.startsWith(r + "/"));

  if (isProtected && !user) {
    return NextResponse.redirect(new URL("/auth/sign-in", request.url));
  }

  return response;
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
```

- [ ] **Step 2: Commit**

```bash
git add frontend/middleware.ts
git commit -m "feat(frontend): protect 5 routes, redirect to /auth/sign-in"
```

---

## Task 22: Frontend — .env.example

**Files:**
- Create: `frontend/.env.example`

- [ ] **Step 1: Write .env.example**

```bash
# frontend/.env.example

# Supabase project URL (from Settings → API) — safe to expose
NEXT_PUBLIC_SUPABASE_URL=https://yourproject.supabase.co

# Supabase anon/public key (from Settings → API) — safe to expose
NEXT_PUBLIC_SUPABASE_ANON_KEY=

# Backend FastAPI URL — change to your Railway URL in production
NEXT_PUBLIC_API_URL=http://localhost:8000
```

- [ ] **Step 2: Commit**

```bash
git add frontend/.env.example
git commit -m "chore(env): add frontend .env.example"
```

---

## Task 23: Makefile

**Files:**
- Create: `Makefile` (repo root)

- [ ] **Step 1: Write Makefile**

```makefile
# Makefile

.PHONY: install dev test lint typecheck format migrations

install:
	cd frontend && npm ci
	cd backend && pip install -r requirements.txt

dev:
	cd frontend && npx concurrently \
		--names "frontend,backend" \
		--prefix-colors "cyan,yellow" \
		"npm run dev" \
		"sh -c 'cd ../backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000'"

test:
	cd backend && python -m pytest tests/ -v
	cd frontend && npm test

lint:
	cd frontend && npm run lint
	cd backend && python -m ruff check app tests

typecheck:
	cd frontend && npx tsc --noEmit
	cd backend && python -m mypy app

format:
	cd frontend && npx prettier --write .
	cd backend && python -m ruff format app tests

migrations:
	python backend/scripts/print_migrations.py
```

- [ ] **Step 2: Commit**

```bash
git add Makefile
git commit -m "chore(make): add Makefile with install, dev, test, lint, typecheck, format, migrations"
```

---

## Task 24: .github/workflows/ci.yml

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create directory and write ci.yml**

```bash
mkdir -p .github/workflows
```

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  frontend:
    name: Frontend (Node 20)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit
      - run: npm test

  backend:
    name: Backend (Python 3.11)
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    env:
      SUPABASE_URL: https://test.supabase.co
      SUPABASE_SERVICE_ROLE_KEY: test-service-role-key
      SUPABASE_ANON_KEY: test-anon-key
      SUPABASE_JWT_SECRET: super-secret-test-jwt-secret-at-least-32-chars!
      GMAIL_CLIENT_ID: test-client-id
      GMAIL_CLIENT_SECRET: test-client-secret
      GMAIL_REDIRECT_URI: http://localhost:8000/auth/gmail/callback
      OAUTH_STATE_SECRET: test-oauth-state-secret-at-least-32-chars!
      OPENAI_API_KEY: sk-test
      FRONTEND_URL: http://localhost:3000
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: backend/requirements.txt
      - run: pip install -r requirements.txt
      - run: python -m ruff check app tests
      - run: python -m mypy app
      - run: python -m pytest tests/ -v
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow for PR lint, typecheck, test"
```

---

## Task 25: README.md — add Migrations subsection

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Migrations subsection to Getting Started**

Find the "Getting Started" section and add after the Supabase step:

```markdown
### Migrations

Run all SQL migrations in order by printing them to stdout:

```bash
python backend/scripts/print_migrations.py
```

Copy the output and paste it into the **Supabase SQL Editor** (Database → SQL Editor → New query). Run once per environment. All migrations are idempotent — safe to re-run.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(readme): add Migrations subsection with print script instructions"
```

---

## Task 26: Verification

Run all quality gates. All must pass before marking Issue 1A complete.

- [ ] **Step 1: Install all deps**

```bash
make install
```

Expected: both `npm ci` and `pip install` complete with no errors.

- [ ] **Step 2: Run backend tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: 10 tests, all PASSED.

- [ ] **Step 3: Run typecheck**

```bash
make typecheck
```

Expected: `tsc` exits 0 (no type errors); `mypy` exits 0.

- [ ] **Step 4: Run lint**

```bash
make lint
```

Expected: `next lint` and `ruff check` both exit 0.

- [ ] **Step 5: Run migrations script**

```bash
make migrations
```

Expected: 6 `-- ===== NNN_xxx.sql =====` headers printed to stdout.

- [ ] **Step 6: Verify service role key not leaked**

```bash
grep -r "service_role_key" backend/app --include="*.py" | grep -v "config.py" | grep -v "supabase.py"
```

Expected: no output (zero matches outside the two allowed files).

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "chore: Issue 1A foundation complete — all tests passing"
```
