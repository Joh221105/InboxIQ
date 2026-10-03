from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import UserClaims, get_current_user
from app.main import app
from app.models.email import PickupCodeRow

_USER_ID = uuid4()


def _override_auth() -> UserClaims:
    return UserClaims(user_id=_USER_ID, email="user@example.com")


@pytest.fixture
def authed_client() -> TestClient:
    app.dependency_overrides[get_current_user] = _override_auth
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_get_pickup_codes_uses_authenticated_user(authed_client: TestClient) -> None:
    item = PickupCodeRow(
        email_id=uuid4(),
        pickup_code="123456",
        pickup_expiry=None,
        pickup_used_at=None,
        retailer="Amazon",
        locker_location="Pine Hub Locker",
        sender_email="ship@amazon.com",
        subject="Your pickup code",
        received_at=datetime(2026, 5, 12, 12, 0, tzinfo=UTC),
    )

    with patch(
        "app.routers.pickup.list_pickup_codes", new_callable=AsyncMock, return_value=[item]
    ) as mock_list:
        response = authed_client.get("/pickup-codes?used=false&include_expired=true")

    assert response.status_code == 200
    assert response.json()["items"][0]["pickup_code"] == "123456"
    mock_list.assert_awaited_once_with(_USER_ID, used=False, include_expired=True)
