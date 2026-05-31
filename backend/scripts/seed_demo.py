#!/usr/bin/env python3
"""Insert demo emails for a live demo.

Usage (from backend/):
    python scripts/seed_demo.py
    python scripts/seed_demo.py --user-id <uuid>
    python scripts/seed_demo.py --clear   # remove all seed emails first
"""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Allow running from the backend/ directory without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from supabase import create_client  # noqa: E402

NOW = datetime.now(timezone.utc)


def days_ago(n: float) -> str:
    return (NOW - timedelta(days=n)).isoformat()


def days_from_now(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()


# ---------------------------------------------------------------------------
# Demo email fixtures
# Each dict maps directly to columns in the emails table.
# gmail_id uses a "demo_" prefix so they're easy to identify and clear.
# ---------------------------------------------------------------------------
DEMO_EMAILS = [
    # ── Package pickup codes ─────────────────────────────────────────────────
    {
        "gmail_id": "demo_pickup_001",
        "subject": "Your Amazon package is ready for pickup",
        "sender": "no-reply@amazon.com",
        "sender_name": "Amazon",
        "snippet": "Pick up your package at Amazon Locker - Pine Hub. Code: 74829",
        "body_text": (
            "Your package has arrived at Amazon Locker - Pine Hub (123 Main St).\n\n"
            "Pickup code: 74829\n"
            "Expires: " + days_from_now(3) + "\n\n"
            "Order: Wireless Keyboard (ASIN B08XYZ123)\n"
            "Scan the code at the locker touchscreen or enter it manually."
        ),
        "received_at": days_ago(0.3),
        "ai_category": "action_required",
        "ai_summary": "Amazon package ready at Pine Hub Locker, use code 74829.",
        "ai_processed": True,
        "is_pickup_code": True,
        "pickup_code": "74829",
        "pickup_expiry": days_from_now(3),
        "retailer": "Amazon",
        "locker_location": "Amazon Locker - Pine Hub, 123 Main St",
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_pickup_002",
        "subject": "FedEx: Package ready at FedEx Office #4821",
        "sender": "TrackingUpdates@fedex.com",
        "sender_name": "FedEx",
        "snippet": "Your package is available for pickup. Confirmation code: FX-39201",
        "body_text": (
            "Hi there,\n\n"
            "Your FedEx package is ready for pickup at:\n"
            "FedEx Office – 456 University Ave\n\n"
            "Confirmation code: FX-39201\n"
            "Hold-by date: " + days_from_now(5) + "\n\n"
            "Tracking: 7489234902834092\n"
            "Shipper: Apple Online Store"
        ),
        "received_at": days_ago(1),
        "ai_category": "action_required",
        "ai_summary": "FedEx package ready at University Ave store, code FX-39201.",
        "ai_processed": True,
        "is_pickup_code": True,
        "pickup_code": "FX-39201",
        "pickup_expiry": days_from_now(5),
        "retailer": "Apple Online Store",
        "locker_location": "FedEx Office – 456 University Ave",
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_pickup_003",
        "subject": "UPS Access Point® Notification",
        "sender": "mc-email@ups.com",
        "sender_name": "UPS",
        "snippet": "Your package is available at The UPS Store #3042. Pickup code: UPS-5512",
        "body_text": (
            "Your package is being held at The UPS Store #3042\n"
            "789 Commerce Blvd, Suite 10\n\n"
            "Pickup code: UPS-5512\n"
            "Available until: " + days_from_now(7) + "\n\n"
            "Tracking: 1Z999AA10123456784\n"
            "Description: Laptop Sleeve"
        ),
        "received_at": days_ago(2),
        "ai_category": "action_required",
        "ai_summary": "UPS package held at The UPS Store #3042, code UPS-5512.",
        "ai_processed": True,
        "is_pickup_code": True,
        "pickup_code": "UPS-5512",
        "pickup_expiry": days_from_now(7),
        "retailer": "UPS",
        "locker_location": "The UPS Store #3042, 789 Commerce Blvd",
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_pickup_004",
        "subject": "USPS: Package held at Post Office",
        "sender": "auto-reply@usps.com",
        "sender_name": "USPS",
        "snippet": "A delivery attempt was made. Package held at Central Post Office.",
        "body_text": (
            "We attempted delivery of your package but no one was available.\n\n"
            "Your package is being held at:\n"
            "Central Post Office – 321 Post St\n\n"
            "Pickup by: " + days_from_now(10) + "\n"
            "You will need a photo ID.\n\n"
            "Tracking: 9400111899223085926400"
        ),
        "received_at": days_ago(1.5),
        "ai_category": "action_required",
        "ai_summary": "USPS package held at Central Post Office, bring photo ID.",
        "ai_processed": True,
        "is_pickup_code": False,
        "pickup_expiry": days_from_now(10),
        "retailer": "USPS",
        "locker_location": "Central Post Office – 321 Post St",
        "labels": ["INBOX"],
    },
    # ── Action required – deadlines ──────────────────────────────────────────
    {
        "gmail_id": "demo_action_001",
        "subject": "Your electric bill is due soon – $94.17",
        "sender": "billing@citypower.example",
        "sender_name": "City Power",
        "snippet": "Payment of $94.17 due by " + days_from_now(3) + " to avoid late fees.",
        "body_text": (
            "Account: 00123-45678\n"
            "Amount due: $94.17\n"
            "Due date: " + days_from_now(3) + "\n\n"
            "Pay online at citypower.example/pay or call 1-800-555-0199.\n"
            "Late fee of $12.50 applies after due date."
        ),
        "received_at": days_ago(2),
        "ai_category": "action_required",
        "ai_summary": "Electric bill of $94.17 due in 3 days, late fee applies.",
        "ai_processed": True,
        "deadline_extracted": days_from_now(3),
        "action_items": ["Pay $94.17 electric bill by " + days_from_now(3)],
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_action_002",
        "subject": "Interview Invitation – Software Engineer @ Anthropic",
        "sender": "recruiting@anthropic.com",
        "sender_name": "Anthropic Recruiting",
        "snippet": "We'd love to schedule a technical interview. Please pick a slot by Friday.",
        "body_text": (
            "Hi,\n\n"
            "We reviewed your application and would love to move forward!\n\n"
            "Please schedule your 45-minute technical interview using the link below:\n"
            "https://calendly.example/anthropic-interview\n\n"
            "Please book by " + days_from_now(2) + ".\n\n"
            "Best,\nAnthropuc Recruiting"
        ),
        "received_at": days_ago(0.5),
        "ai_category": "action_required",
        "ai_summary": "Anthropic invites you to schedule a technical interview by Friday.",
        "ai_processed": True,
        "deadline_extracted": days_from_now(2),
        "action_items": ["Book interview slot by " + days_from_now(2)],
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_action_003",
        "subject": "Action Required: Complete your online assessment",
        "sender": "no-reply@hirevue.example",
        "sender_name": "HireVue",
        "snippet": "Complete your assessment for Google SWE role. Expires in 48 hours.",
        "body_text": (
            "You have been invited to complete an online assessment for:\n"
            "Google – Software Engineer, L4\n\n"
            "Deadline: " + days_from_now(2) + " at 11:59 PM Pacific\n\n"
            "The assessment takes approximately 90 minutes.\n"
            "Start here: https://hirevue.example/start/abc123\n\n"
            "Do not share this link."
        ),
        "received_at": days_ago(0.2),
        "ai_category": "action_required",
        "ai_summary": "Google OA due in 48 hours – 90 minutes, do not delay.",
        "ai_processed": True,
        "deadline_extracted": days_from_now(2),
        "action_items": ["Complete Google OA by " + days_from_now(2)],
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_action_004",
        "subject": "Your subscription renews in 3 days – update payment",
        "sender": "billing@notion.so",
        "sender_name": "Notion",
        "snippet": "Your Notion Plus plan renews on " + days_from_now(3) + ". Card ending 4242 may fail.",
        "body_text": (
            "Your Notion Plus subscription renews on " + days_from_now(3) + ".\n\n"
            "We'll charge the card ending in 4242. If payment fails your workspace "
            "will be downgraded to Free.\n\n"
            "Update payment: https://notion.so/settings/billing"
        ),
        "received_at": days_ago(1),
        "ai_category": "action_required",
        "ai_summary": "Notion Plus renews in 3 days; update card to avoid downgrade.",
        "ai_processed": True,
        "deadline_extracted": days_from_now(3),
        "action_items": ["Update payment method at notion.so/settings/billing"],
        "labels": ["INBOX"],
    },
    # ── Worth reading ────────────────────────────────────────────────────────
    {
        "gmail_id": "demo_read_001",
        "subject": "Your order has shipped! Track #1Z-ABC-1234",
        "sender": "shipment-tracking@amazon.com",
        "sender_name": "Amazon",
        "snippet": "Your Sony WH-1000XM5 headphones are on their way.",
        "body_text": (
            "Great news! Your package is on its way.\n\n"
            "Item: Sony WH-1000XM5 Wireless Headphones\n"
            "Carrier: UPS\n"
            "Tracking: 1Z-ABC-1234\n"
            "Estimated delivery: " + days_from_now(2) + "\n\n"
            "Track your package: https://ups.com/track?num=1ZABC1234"
        ),
        "received_at": days_ago(1),
        "ai_category": "worth_reading",
        "ai_summary": "Sony WH-1000XM5 shipped via UPS, estimated delivery in 2 days.",
        "ai_processed": True,
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_read_002",
        "subject": "Order Confirmed – #112-3456789-0123456",
        "sender": "order-update@amazon.com",
        "sender_name": "Amazon",
        "snippet": "Thank you for your order. MX Master 3S Mouse – $99.99",
        "body_text": (
            "Thank you for your order!\n\n"
            "Order #112-3456789-0123456\n"
            "Item: Logitech MX Master 3S Mouse – $99.99\n"
            "Estimated delivery: " + days_from_now(4) + "\n\n"
            "Shipping to: 123 Demo St, Seattle, WA 98101"
        ),
        "received_at": days_ago(0.8),
        "ai_category": "worth_reading",
        "ai_summary": "Amazon order confirmed: Logitech MX Master 3S, arrives in 4 days.",
        "ai_processed": True,
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_read_003",
        "subject": "Application received – Product Manager at Stripe",
        "sender": "no-reply@stripe.com",
        "sender_name": "Stripe Recruiting",
        "snippet": "Thanks for applying! We'll review your materials and follow up within 2 weeks.",
        "body_text": (
            "Hi,\n\n"
            "We've received your application for Product Manager at Stripe.\n\n"
            "Our team will review your materials and reach out within 2 weeks if we'd "
            "like to move forward.\n\n"
            "Thanks for your interest!\nStripe Recruiting"
        ),
        "received_at": days_ago(3),
        "ai_category": "worth_reading",
        "ai_summary": "Stripe confirmed receipt of PM application, will follow up in 2 weeks.",
        "ai_processed": True,
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_read_004",
        "subject": "Refund processed – $34.99 returned to your card",
        "sender": "noreply@bestbuy.com",
        "sender_name": "Best Buy",
        "snippet": "Your refund of $34.99 is on its way to your Visa ending in 1234.",
        "body_text": (
            "Your refund has been processed.\n\n"
            "Amount: $34.99\n"
            "Returned to: Visa ending in 1234\n"
            "Please allow 3–5 business days to appear on your statement.\n\n"
            "Return confirmation: BBY-RET-20240531"
        ),
        "received_at": days_ago(2.5),
        "ai_category": "worth_reading",
        "ai_summary": "Best Buy refund of $34.99 processed; allow 3–5 business days.",
        "ai_processed": True,
        "labels": ["INBOX"],
    },
    # ── Auto-archive (newsletters, promo) ────────────────────────────────────
    {
        "gmail_id": "demo_archive_001",
        "subject": "10 new Software Engineer jobs match your profile",
        "sender": "jobs-noreply@linkedin.com",
        "sender_name": "LinkedIn Jobs",
        "snippet": "Anthropic, OpenAI, Google and 7 more are hiring.",
        "body_text": (
            "Based on your profile, these companies are hiring:\n\n"
            "• Anthropic – Research Engineer\n"
            "• OpenAI – Backend Engineer\n"
            "• Google – SWE L4\n"
            "+ 7 more matches\n\n"
            "View all: https://linkedin.com/jobs"
        ),
        "received_at": days_ago(4),
        "ai_category": "auto_archive",
        "ai_summary": "LinkedIn weekly digest of 10 new Software Engineer job postings.",
        "ai_processed": True,
        "is_archived": True,
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_archive_002",
        "subject": "Memorial Day Sale – Up to 60% off sitewide",
        "sender": "deals@gap.com",
        "sender_name": "Gap",
        "snippet": "Shop our biggest sale of the year. Ends Monday.",
        "body_text": (
            "It's our biggest sale of the year!\n\n"
            "60% off full-price styles\n"
            "40% off sale styles\n"
            "Free shipping on orders over $50\n\n"
            "Shop now: https://gap.com/sale"
        ),
        "received_at": days_ago(5),
        "ai_category": "auto_archive",
        "ai_summary": "Gap Memorial Day sale offers up to 60% off sitewide through Monday.",
        "ai_processed": True,
        "is_archived": True,
        "labels": ["INBOX", "CATEGORY_PROMOTIONS"],
    },
    {
        "gmail_id": "demo_archive_003",
        "subject": "The Weekly Dev Digest – Issue #142",
        "sender": "noreply@tldr.tech",
        "sender_name": "TLDR Newsletter",
        "snippet": "This week: new React 19 features, Rust wins StackOverflow survey again.",
        "body_text": (
            "TLDR Newsletter – Issue #142\n\n"
            "• React 19 ships with new concurrent features\n"
            "• Rust tops StackOverflow survey for 9th year\n"
            "• OpenAI releases new API pricing tiers\n"
            "• 12 more stories inside\n\n"
            "Read online: https://tldr.tech/142"
        ),
        "received_at": days_ago(6),
        "ai_category": "auto_archive",
        "ai_summary": "TLDR weekly dev newsletter covers React 19, Rust, and OpenAI news.",
        "ai_processed": True,
        "is_archived": True,
        "labels": ["INBOX"],
    },
    # ── School / deadline context ─────────────────────────────────────────────
    {
        "gmail_id": "demo_school_001",
        "subject": "Admission Decision Available – University of Washington",
        "sender": "admissions@uw.edu",
        "sender_name": "UW Admissions",
        "snippet": "Your admission decision for the MS CS program is ready. Respond by June 15.",
        "body_text": (
            "Dear Applicant,\n\n"
            "Your admission decision for the UW Master of Science in Computer Science "
            "program is now available in your application portal.\n\n"
            "Please log in and submit your intent to enroll by " + days_from_now(15) + ".\n\n"
            "Portal: https://apply.uw.edu\n\n"
            "Congratulations!"
        ),
        "received_at": days_ago(1.2),
        "ai_category": "action_required",
        "ai_summary": "UW MS CS admission decision ready; respond with intent by " + days_from_now(15) + ".",
        "ai_processed": True,
        "deadline_extracted": days_from_now(15),
        "action_items": ["Log in to apply.uw.edu and submit enrollment intent by " + days_from_now(15)],
        "labels": ["INBOX"],
    },
    {
        "gmail_id": "demo_school_002",
        "subject": "Financial Aid Award Letter – $18,500 for 2026–27",
        "sender": "finaid@uw.edu",
        "sender_name": "UW Financial Aid",
        "snippet": "Your financial aid package for 2026–27 is ready to review.",
        "body_text": (
            "Dear Student,\n\n"
            "Your financial aid award for the 2026–27 academic year has been posted.\n\n"
            "Award breakdown:\n"
            "• Federal Direct Subsidized Loan: $5,500\n"
            "• University Merit Scholarship: $10,000\n"
            "• Work-Study: $3,000\n"
            "Total: $18,500\n\n"
            "Accept or decline at: https://myuw.edu/finaid"
        ),
        "received_at": days_ago(3),
        "ai_category": "worth_reading",
        "ai_summary": "UW financial aid award of $18,500 for 2026–27 is ready to review.",
        "ai_processed": True,
        "labels": ["INBOX"],
    },
]


def get_account_id(client, user_id: str) -> str:
    result = (
        client.table("connected_accounts")
        .select("id")
        .eq("user_id", user_id)
        .is_("disconnected_at", "null")
        .order("created_at")
        .limit(1)
        .execute()
    )
    if not result.data:
        print(f"ERROR: No connected account found for user {user_id}.")
        print("Connect a Gmail account in the app first, then re-run this script.")
        sys.exit(1)
    return result.data[0]["id"]


def seed(user_id: str, clear: bool = False) -> None:
    client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    account_id = get_account_id(client, user_id)
    print(f"Using account {account_id} for user {user_id}")

    if clear:
        result = (
            client.table("emails")
            .delete()
            .eq("user_id", user_id)
            .like("gmail_id", "demo_%")
            .execute()
        )
        count = len(result.data) if result.data else 0
        print(f"Cleared {count} existing demo emails.")

    rows = [
        {
            **email,
            "user_id": user_id,
            "account_id": account_id,
            "action_items": email.get("action_items", []),
            "is_archived": email.get("is_archived", False),
            "is_read": email.get("is_read", False),
            "is_pickup_code": email.get("is_pickup_code", False),
            "pickup_used": False,
            "labels": email.get("labels", ["INBOX"]),
        }
        for email in DEMO_EMAILS
    ]

    result = (
        client.table("emails")
        .upsert(rows, on_conflict="account_id,gmail_id")
        .execute()
    )
    count = len(result.data) if result.data else 0
    print(f"Seeded {count} demo emails.")

    categories = {}
    for e in DEMO_EMAILS:
        cat = e.get("ai_category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    for cat, n in sorted(categories.items()):
        print(f"  {cat}: {n}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo emails for InboxIQ")
    parser.add_argument("--user-id", default="4b02cc6c-1d4b-487d-bb4e-8e09b7fab755",
                        help="Supabase user UUID")
    parser.add_argument("--clear", action="store_true",
                        help="Delete existing demo emails before inserting")
    args = parser.parse_args()
    seed(args.user_id, clear=args.clear)


if __name__ == "__main__":
    main()
