from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.email import Email
from app.services.triage import pickup_code_prefilter


def _email(text: str) -> Email:
    return Email(
        id=uuid4(),
        user_id=uuid4(),
        account_id=uuid4(),
        gmail_id=uuid4().hex,
        subject=text,
        sender="sender@example.com",
        received_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
        body_text=text,
        created_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
    )


@pytest.mark.parametrize(
    "text",
    [
        "Your Amazon Locker pickup code is 1234 5678",
        "Amazon Hub package is waiting",
        "Amazon locker delivery notice",
        "FedEx - Ready for pickup",
        "FedEx hold at location",
        "UPS Access Point notification",
        "USPS held mail reminder",
        "DHL ServicePoint pickup notice",
        "Your pickup code is available",
        "Ready for pickup at the counter",
        "codigo de recogida: 1234",
        "código de recogida: 1234",
        "DHL pickup instructions",
        "FedEx pickup barcode",
        "Amazon Hub Counter code",
        "UPS access point ready",
    ],
)
def test_pickup_prefilter_true_cases(text: str) -> None:
    assert pickup_code_prefilter(_email(text)) is True


@pytest.mark.parametrize(
    "text",
    [
        "Your Amazon order has shipped",
        "Sale this Friday only",
        "Job alert: 10 new postings",
        "Your package is out for delivery",
        "Informed Delivery daily digest",
        "LinkedIn weekly jobs update",
        "Order confirmation",
        "Your receipt from Target",
        "Black Friday deals",
        "Application received",
        "Newsletter: campus events",
        "Subscription renewal notice",
        "Your statement is ready",
        "Security tips for your account",
        "Package delivered",
        "Shipping label created",
    ],
)
def test_pickup_prefilter_false_cases(text: str) -> None:
    assert pickup_code_prefilter(_email(text)) is False


@pytest.mark.parametrize(
    "subject,body",
    [
        (
            "Amazon Locker Pickup Reminder",
            (
                "Hello, your package is ready for pickup at Amazon Hub Locker - Maple Station. "
                "Pickup code: 9021 7744. Bring this code to open the locker. "
                "Code expires in 2 days."
            ),
        ),
        (
            "FedEx Hold at Location: Ready for pickup",
            (
                "Your shipment is now available for pickup at the FedEx Office location. "
                "Use pickup code 44A7B9 and bring a government-issued ID."
            ),
        ),
    ],
)
def test_pickup_prefilter_detects_realistic_provider_samples(subject: str, body: str) -> None:
    email = _email(subject)
    email.body_text = body
    assert pickup_code_prefilter(email) is True
