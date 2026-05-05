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
