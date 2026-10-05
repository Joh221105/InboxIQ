from __future__ import annotations

import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from app.models.email import Email
from app.services.triage import triage_email

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_AI_QUALITY_TESTS") != "1",
    reason="Set RUN_AI_QUALITY_TESTS=1 to run real LLM quality tests.",
)


def _load_fixtures() -> list[dict]:
    fixtures_dir = Path(__file__).parent / "fixtures"
    return [json.loads(path.read_text()) for path in sorted(fixtures_dir.glob("*.json"))]


@pytest.mark.asyncio
async def test_triage_category_accuracy() -> None:
    fixtures = _load_fixtures()
    results: list[tuple[str, str]] = []

    for fixture in fixtures:
        raw = fixture["email"]
        email = Email(
            id=uuid4(),
            user_id=uuid4(),
            account_id=uuid4(),
            gmail_id=uuid4().hex,
            subject=raw["subject"],
            sender=raw["from"],
            body_text=raw["body"],
            received_at=datetime(2026, 5, 13, tzinfo=UTC),
            created_at=datetime(2026, 5, 13, tzinfo=UTC),
        )
        actual = await triage_email(email, fixture["context"])
        results.append((fixture["expected_category"], actual.category))

    correct = sum(1 for expected, actual in results if expected == actual)
    accuracy = correct / len(results)
    matrix = Counter(results)
    print("Confusion matrix:")
    for (expected, actual), count in sorted(matrix.items()):
        print(f"{expected} -> {actual}: {count}")
    assert accuracy >= 0.85
