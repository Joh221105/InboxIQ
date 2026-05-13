from __future__ import annotations

import os

# Must be set before any app module is imported
for key, value in {
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
}.items():
    os.environ.setdefault(key, value)

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
