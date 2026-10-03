"""Supabase access for the backend.

The service-role client bypasses row-level security, so every query in
``app.db`` must filter by the verified user's id. RLS policies remain the
second line of defense. The client is never exposed to the frontend.
"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from supabase import Client, create_client


@lru_cache(maxsize=1)
def get_service_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
