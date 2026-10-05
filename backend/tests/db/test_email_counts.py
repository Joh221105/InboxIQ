from __future__ import annotations

from uuid import uuid4

import httpx
import respx

from app.db import emails as emails_db
from app.db.emails import get_email_counts
from supabase import Client
from tests.db.test_query_builders import REST, real_client  # noqa: F401  (fixture)

TOTALS = {None: 2500, "action_required": 40, "worth_reading": 300, "auto_archive": 2160}


@respx.mock
async def test_counts_come_from_content_range_without_a_row_cap(real_client: Client) -> None:  # noqa: F811
    emails_db._counts_cache.clear()

    def respond(request: httpx.Request) -> httpx.Response:
        category = request.url.params.get("ai_category")
        total = TOTALS[category.removeprefix("eq.") if category else None]
        headers = {"Content-Range": f"0-0/{total}"}
        if request.method == "HEAD":  # PostgREST sends no body for HEAD
            return httpx.Response(200, headers=headers)
        return httpx.Response(200, json=[{"id": "x"}], headers=headers)

    respx.route(url__startswith=f"{REST}/emails").mock(side_effect=respond)

    counts = await get_email_counts(uuid4())

    assert counts.model_dump() == {
        "all": 2500,
        "action_required": 40,
        "worth_reading": 300,
        "auto_archive": 2160,
    }
