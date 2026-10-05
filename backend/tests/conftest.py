from __future__ import annotations

import os

# Must be set before any app module is imported
for key, value in {
    "SUPABASE_URL": "https://testproject.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key-long-enough-here",
    "SUPABASE_JWT_SECRET": "super-secret-test-jwt-secret-at-least-32-chars!",
    "GMAIL_CLIENT_ID": "test-gmail-client-id.apps.googleusercontent.com",
    "GMAIL_CLIENT_SECRET": "test-gmail-client-secret",
    "GMAIL_REDIRECT_URI": "http://localhost:8000/auth/gmail/callback",
    "OAUTH_STATE_SECRET": "test-oauth-state-secret-at-least-32-chars!",
    "OPENROUTER_API_KEY": "test-openrouter-key",
    "FRONTEND_URL": "http://localhost:3000",
}.items():
    os.environ.setdefault(key, value)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
