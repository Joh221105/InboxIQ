"""Demo email seed data and helper to insert it.

Called automatically after a Gmail account is connected so the inbox
is populated with realistic content for demos and first-time users.
All demo rows use a ``demo_`` prefix on ``gmail_id`` so they can be
identified and re-seeded idempotently.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from app.db.supabase import get_service_client

logger = logging.getLogger(__name__)

_NOW = None  # resolved lazily per call so dates are always current


def _now() -> datetime:
    return datetime.now(UTC)


def _days_ago(n: float) -> str:
    return (_now() - timedelta(days=n)).isoformat()


def _days_from_now(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()


def _build_emails() -> list[dict]:
    """Build demo email fixtures. Called at seed time so all dates are fresh."""
    return [
        # ── Package pickup codes ─────────────────────────────────────────────
        {
            "gmail_id": "demo_pickup_001",
            "subject": "Your Amazon package is ready for pickup",
            "sender": "no-reply@amazon.com",
            "sender_name": "Amazon",
            "snippet": "Pick up your package at Amazon Locker - Pine Hub. Code: 74829",
            "body_text": (
                "Your package has arrived at Amazon Locker - Pine Hub (123 Main St).\n\n"
                "Pickup code: 74829\n"
                f"Expires: {_days_from_now(3)}\n\n"
                "Order: Wireless Keyboard (ASIN B08XYZ123)\n"
                "Scan the code at the locker touchscreen or enter it manually."
            ),
            "received_at": _days_ago(0.3),
            "ai_category": "action_required",
            "ai_summary": "Amazon package ready at Pine Hub Locker — use code 74829.",
            "ai_processed": True,
            "is_pickup_code": True,
            "pickup_code": "74829",
            "pickup_expiry": _days_from_now(3),
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
                f"Hold-by date: {_days_from_now(5)}\n\n"
                "Tracking: 7489234902834092\n"
                "Shipper: Apple Online Store"
            ),
            "received_at": _days_ago(1),
            "ai_category": "action_required",
            "ai_summary": "FedEx package ready at University Ave store — code FX-39201.",
            "ai_processed": True,
            "is_pickup_code": True,
            "pickup_code": "FX-39201",
            "pickup_expiry": _days_from_now(5),
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
                f"Available until: {_days_from_now(7)}\n\n"
                "Tracking: 1Z999AA10123456784\n"
                "Description: Laptop Sleeve"
            ),
            "received_at": _days_ago(2),
            "ai_category": "action_required",
            "ai_summary": "UPS package held at The UPS Store #3042 — code UPS-5512.",
            "ai_processed": True,
            "is_pickup_code": True,
            "pickup_code": "UPS-5512",
            "pickup_expiry": _days_from_now(7),
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
                f"Pickup by: {_days_from_now(10)}\n"
                "You will need a photo ID.\n\n"
                "Tracking: 9400111899223085926400"
            ),
            "received_at": _days_ago(1.5),
            "ai_category": "action_required",
            "ai_summary": "USPS package held at Central Post Office — bring photo ID.",
            "ai_processed": True,
            "is_pickup_code": False,
            "pickup_expiry": _days_from_now(10),
            "retailer": "USPS",
            "locker_location": "Central Post Office – 321 Post St",
            "labels": ["INBOX"],
        },
        # ── Action required – deadlines ──────────────────────────────────────
        {
            "gmail_id": "demo_action_001",
            "subject": "Your electric bill is due soon – $94.17",
            "sender": "billing@citypower.example",
            "sender_name": "City Power",
            "snippet": f"Payment of $94.17 due by {_days_from_now(3)} to avoid late fees.",
            "body_text": (
                "Account: 00123-45678\n"
                "Amount due: $94.17\n"
                f"Due date: {_days_from_now(3)}\n\n"
                "Pay online at citypower.example/pay or call 1-800-555-0199.\n"
                "Late fee of $12.50 applies after due date."
            ),
            "received_at": _days_ago(2),
            "ai_category": "action_required",
            "ai_summary": "Electric bill of $94.17 due in 3 days — late fee applies.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(3),
            "action_items": [f"Pay $94.17 electric bill by {_days_from_now(3)}"],
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
                f"Please book by {_days_from_now(2)}.\n\n"
                "Best,\nAnthropuc Recruiting"
            ),
            "received_at": _days_ago(0.5),
            "ai_category": "action_required",
            "ai_summary": "Anthropic invites you to schedule a technical interview by Friday.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(2),
            "action_items": [
                f"Book interview slot at calendly.example/anthropic-interview by {_days_from_now(2)}"
            ],
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
                f"Deadline: {_days_from_now(2)} at 11:59 PM Pacific\n\n"
                "The assessment takes approximately 90 minutes.\n"
                "Start here: https://hirevue.example/start/abc123\n\n"
                "Do not share this link."
            ),
            "received_at": _days_ago(0.2),
            "ai_category": "action_required",
            "ai_summary": "Google OA due in 48 hours – 90 minutes, do not delay.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(2),
            "action_items": [f"Complete Google SWE OA at hirevue.example by {_days_from_now(2)}"],
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_action_004",
            "subject": "Your subscription renews in 3 days – update payment",
            "sender": "billing@notion.so",
            "sender_name": "Notion",
            "snippet": f"Your Notion Plus plan renews on {_days_from_now(3)}. Card ending 4242 may fail.",
            "body_text": (
                f"Your Notion Plus subscription renews on {_days_from_now(3)}.\n\n"
                "We'll charge the card ending in 4242. If payment fails your workspace "
                "will be downgraded to Free.\n\n"
                "Update payment: https://notion.so/settings/billing"
            ),
            "received_at": _days_ago(1),
            "ai_category": "action_required",
            "ai_summary": "Notion Plus renews in 3 days — update card to avoid downgrade.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(3),
            "action_items": ["Update payment method at notion.so/settings/billing"],
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_action_005",
            "subject": "Lease Renewal – Response needed by " + _days_from_now(6),
            "sender": "leasing@greenpointapts.example",
            "sender_name": "Greenpoint Apartments",
            "snippet": f"Please sign or decline your lease renewal by {_days_from_now(6)}.",
            "body_text": (
                "Dear Resident,\n\n"
                "Your current lease expires on " + _days_from_now(30) + ".\n\n"
                "Renewal terms:\n"
                "  • 12-month lease: $1,850/month (no increase)\n"
                "  • 6-month lease: $1,950/month\n\n"
                f"Please sign or decline via the resident portal by {_days_from_now(6)}:\n"
                "https://greenpointapts.example/portal\n\n"
                "Questions? Contact leasing@greenpointapts.example or call (555) 310-2200."
            ),
            "received_at": _days_ago(1.2),
            "ai_category": "action_required",
            "ai_summary": "Apartment lease renewal decision due in 6 days — sign or decline online.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(6),
            "action_items": [
                f"Sign or decline lease renewal at greenpointapts.example/portal by {_days_from_now(6)}"
            ],
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_action_006",
            "subject": "FINAL NOTICE: Complete I-9 verification by " + _days_from_now(1),
            "sender": "hr@techcorp.example",
            "sender_name": "TechCorp HR",
            "snippet": "Federal law requires I-9 completion before your start date. Due tomorrow.",
            "body_text": (
                "Hi,\n\n"
                "This is a final reminder that your Form I-9 employment eligibility "
                "verification must be completed before you can start on "
                + _days_from_now(4)
                + ".\n\n"
                f"Deadline: {_days_from_now(1)}\n\n"
                "Please bring two forms of acceptable ID to the HR office (Building A, Room 101) "
                "or complete remotely via: https://hris.techcorp.example/i9\n\n"
                "Failure to complete this by the deadline will delay your start date."
            ),
            "received_at": _days_ago(0.4),
            "ai_category": "action_required",
            "ai_summary": "I-9 verification due tomorrow — required before start date.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(1),
            "action_items": [
                f"Complete I-9 at hris.techcorp.example/i9 by {_days_from_now(1)}",
                "Bring two forms of ID to HR (Building A, Room 101)",
            ],
            "labels": ["INBOX"],
        },
        # ── Worth reading ────────────────────────────────────────────────────
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
                f"Estimated delivery: {_days_from_now(2)}\n\n"
                "Track your package: https://ups.com/track?num=1ZABC1234"
            ),
            "received_at": _days_ago(1),
            "ai_category": "worth_reading",
            "ai_summary": "Sony WH-1000XM5 shipped via UPS — estimated delivery in 2 days.",
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
                f"Estimated delivery: {_days_from_now(4)}\n\n"
                "Shipping to: 123 Demo St, Seattle, WA 98101"
            ),
            "received_at": _days_ago(0.8),
            "ai_category": "worth_reading",
            "ai_summary": "Amazon order confirmed: Logitech MX Master 3S — arrives in 4 days.",
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
                "Our team will review your materials and reach out within 2 weeks if "
                "we'd like to move forward.\n\n"
                "Thanks for your interest!\nStripe Recruiting"
            ),
            "received_at": _days_ago(3),
            "ai_category": "worth_reading",
            "ai_summary": "Stripe confirmed receipt of PM application — will follow up in 2 weeks.",
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
            "received_at": _days_ago(2.5),
            "ai_category": "worth_reading",
            "ai_summary": "Best Buy refund of $34.99 processed — allow 3–5 business days.",
            "ai_processed": True,
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_read_005",
            "subject": "We've received your application – Figma",
            "sender": "recruiting@figma.com",
            "sender_name": "Figma Recruiting",
            "snippet": "Thanks for applying to Software Engineer, Infra at Figma.",
            "body_text": (
                "Hi,\n\n"
                "Thank you for applying to the Software Engineer, Infrastructure role at Figma.\n\n"
                "Your application has been received and will be reviewed by our recruiting team. "
                "We typically get back to candidates within 1–2 weeks.\n\n"
                "In the meantime, feel free to explore life at Figma:\n"
                "https://figma.com/careers\n\n"
                "Best,\nFigma Recruiting"
            ),
            "received_at": _days_ago(4),
            "ai_category": "worth_reading",
            "ai_summary": "Figma acknowledged SWE Infra application — response in 1–2 weeks.",
            "ai_processed": True,
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_read_006",
            "subject": "Your GitHub Copilot subscription is active",
            "sender": "noreply@github.com",
            "sender_name": "GitHub",
            "snippet": "You're now subscribed to GitHub Copilot Individual – $10/month.",
            "body_text": (
                "Hey there,\n\n"
                "Your GitHub Copilot Individual subscription is now active.\n\n"
                "Plan: Copilot Individual\n"
                "Price: $10.00/month\n"
                f"Next billing date: {_days_from_now(28)}\n\n"
                "Get started in VS Code: open the Extensions panel and search for "
                "'GitHub Copilot'.\n\n"
                "Manage subscription: https://github.com/settings/copilot"
            ),
            "received_at": _days_ago(1.5),
            "ai_category": "worth_reading",
            "ai_summary": "GitHub Copilot Individual subscription activated at $10/month.",
            "ai_processed": True,
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_read_007",
            "subject": "Phone screen scheduled – Meta, Tuesday 2 PM PT",
            "sender": "recruiting@meta.com",
            "sender_name": "Meta Recruiting",
            "snippet": "Your phone screen with Meta is confirmed for Tuesday at 2 PM Pacific.",
            "body_text": (
                "Hi,\n\n"
                "Your phone screen with Meta Recruiting is confirmed!\n\n"
                f"Date: {_days_from_now(5)}\n"
                "Time: 2:00 PM – 2:30 PM Pacific Time\n"
                "Format: Phone call (recruiter will call your number on file)\n\n"
                "What to expect:\n"
                "  • 5 min intro\n"
                "  • 15 min background & motivation\n"
                "  • 10 min Q&A\n\n"
                "Role: Software Engineer – Ads Infrastructure\n\n"
                "Need to reschedule? Reply to this email at least 24 hours in advance.\n\n"
                "Good luck!"
            ),
            "received_at": _days_ago(0.7),
            "ai_category": "worth_reading",
            "ai_summary": f"Meta phone screen confirmed for {_days_from_now(5)} at 2 PM PT.",
            "ai_processed": True,
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_read_008",
            "subject": "Your rent payment of $1,850 was received",
            "sender": "noreply@greenpointapts.example",
            "sender_name": "Greenpoint Apartments",
            "snippet": "Payment of $1,850.00 received for June rent. Thank you.",
            "body_text": (
                "Payment Confirmation\n\n"
                "Amount: $1,850.00\n"
                "For: June rent – Apt 4B\n"
                f"Date received: {_days_ago(1)[:10]}\n"
                "Confirmation: GP-2024-06-12345\n\n"
                "Your account balance is $0.00.\n\n"
                "Thank you for your timely payment!"
            ),
            "received_at": _days_ago(1),
            "ai_category": "worth_reading",
            "ai_summary": "June rent of $1,850 confirmed received — account balance $0.",
            "ai_processed": True,
            "labels": ["INBOX"],
        },
        # ── Auto-archive (newsletters, promo) ────────────────────────────────
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
            "received_at": _days_ago(4),
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
            "received_at": _days_ago(5),
            "ai_category": "auto_archive",
            "ai_summary": "Gap Memorial Day sale — up to 60% off sitewide through Monday.",
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
            "received_at": _days_ago(6),
            "ai_category": "auto_archive",
            "ai_summary": "TLDR weekly dev newsletter covers React 19, Rust, and OpenAI news.",
            "ai_processed": True,
            "is_archived": True,
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_archive_004",
            "subject": "Your Spotify Wrapped is here 🎉",
            "sender": "no-reply@spotify.com",
            "sender_name": "Spotify",
            "snippet": "You listened to 47,203 minutes of music this year. See your stats.",
            "body_text": (
                "Your 2024 Wrapped is here!\n\n"
                "Minutes listened: 47,203\n"
                "Top artist: Hozier\n"
                "Top song: Too Sweet\n"
                "Top genre: Indie Folk\n"
                "Top podcast: Lex Fridman Podcast\n\n"
                "See your full Wrapped: https://spotify.com/wrapped"
            ),
            "received_at": _days_ago(7),
            "ai_category": "auto_archive",
            "ai_summary": "Spotify Wrapped 2024 is ready — 47,203 minutes listened this year.",
            "ai_processed": True,
            "is_archived": True,
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_archive_005",
            "subject": "Your Amazon Prime membership renews automatically",
            "sender": "no-reply@amazon.com",
            "sender_name": "Amazon",
            "snippet": "Your Prime membership will automatically renew on "
            + _days_from_now(14)
            + ".",
            "body_text": (
                "Hi,\n\n"
                f"Your Amazon Prime membership will renew automatically on {_days_from_now(14)} "
                "for $14.99/month.\n\n"
                "No action is required. Your current payment method (Visa ending in 4242) "
                "will be charged.\n\n"
                "To cancel or manage: https://amazon.com/prime\n\n"
                "Thank you for being a Prime member!"
            ),
            "received_at": _days_ago(3),
            "ai_category": "auto_archive",
            "ai_summary": "Amazon Prime auto-renews in 14 days for $14.99 — no action needed.",
            "ai_processed": True,
            "is_archived": True,
            "labels": ["INBOX"],
        },
        # ── School / academic ─────────────────────────────────────────────────
        {
            "gmail_id": "demo_school_001",
            "subject": "Admission Decision Available – University of Washington",
            "sender": "admissions@uw.edu",
            "sender_name": "UW Admissions",
            "snippet": "Your admission decision for the MS CS program is ready. Respond by "
            + _days_from_now(15)
            + ".",
            "body_text": (
                "Dear Applicant,\n\n"
                "Your admission decision for the UW Master of Science in Computer Science "
                "program is now available in your application portal.\n\n"
                f"Please log in and submit your intent to enroll by {_days_from_now(15)}.\n\n"
                "Portal: https://apply.uw.edu\n\n"
                "Congratulations!"
            ),
            "received_at": _days_ago(1.2),
            "ai_category": "action_required",
            "ai_summary": f"UW MS CS admission decision ready — submit enrollment intent by {_days_from_now(15)}.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(15),
            "action_items": [
                f"Log in to apply.uw.edu and submit enrollment intent by {_days_from_now(15)}"
            ],
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
                "  • Federal Direct Subsidized Loan: $5,500\n"
                "  • University Merit Scholarship: $10,000\n"
                "  • Work-Study: $3,000\n"
                "Total: $18,500\n\n"
                "Accept or decline at: https://myuw.edu/finaid"
            ),
            "received_at": _days_ago(3),
            "ai_category": "worth_reading",
            "ai_summary": "UW financial aid award of $18,500 for 2026–27 is ready to review.",
            "ai_processed": True,
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_school_003",
            "subject": "Assignment 3 due " + _days_from_now(3) + " – CSE 521",
            "sender": "noreply@canvas.uw.edu",
            "sender_name": "Canvas LMS",
            "snippet": "Assignment 3: Graph Algorithms is due "
            + _days_from_now(3)
            + " at 11:59 PM.",
            "body_text": (
                "A reminder from Canvas:\n\n"
                "Course: CSE 521 – Algorithms\n"
                "Assignment: Assignment 3 — Graph Algorithms (BFS, Dijkstra, Bellman-Ford)\n"
                f"Due: {_days_from_now(3)} at 11:59 PM Pacific\n\n"
                "Submission format: PDF via Gradescope\n"
                "Late policy: 10% deduction per day, max 3 days late\n\n"
                "Submit here: https://canvas.uw.edu/courses/521/assignments/3"
            ),
            "received_at": _days_ago(0.5),
            "ai_category": "action_required",
            "ai_summary": f"CSE 521 Assignment 3 (Graph Algorithms) due {_days_from_now(3)} at 11:59 PM.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(3),
            "action_items": [
                f"Submit CSE 521 Assignment 3 on Gradescope by {_days_from_now(3)} 11:59 PM"
            ],
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_school_004",
            "subject": "Grade posted: Midterm Exam – CSE 521",
            "sender": "noreply@gradescope.com",
            "sender_name": "Gradescope",
            "snippet": "Your midterm grade for CSE 521 has been released.",
            "body_text": (
                "Your grade for CSE 521 – Algorithms Midterm Exam has been released.\n\n"
                "Score: 87 / 100\n"
                "Class mean: 74.3\n"
                "Class median: 76\n\n"
                "View your submission and feedback:\n"
                "https://gradescope.com/courses/521/assignments/midterm\n\n"
                "Regrade requests close in 7 days."
            ),
            "received_at": _days_ago(2),
            "ai_category": "worth_reading",
            "ai_summary": "CSE 521 midterm grade: 87/100 (class mean 74.3) — regrade window open 7 days.",
            "ai_processed": True,
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_school_005",
            "subject": "Office Hours Cancelled – Prof. Chen – " + _days_from_now(1),
            "sender": "mchen@cs.uw.edu",
            "sender_name": "Prof. Michelle Chen",
            "snippet": "Tomorrow's office hours are cancelled. Next session "
            + _days_from_now(8)
            + ".",
            "body_text": (
                "Hi everyone,\n\n"
                f"I need to cancel my office hours scheduled for {_days_from_now(1)} due to a "
                "department meeting conflict.\n\n"
                f"Next office hours will be as usual on {_days_from_now(8)}, 2–4 PM in CSE 412.\n\n"
                "For urgent questions, please post on Ed Discussion and I'll respond within 24 hours.\n\n"
                "Apologies for the inconvenience.\n\n"
                "— Prof. Chen"
            ),
            "received_at": _days_ago(0.2),
            "ai_category": "worth_reading",
            "ai_summary": f"Prof. Chen cancelled tomorrow's office hours — next session {_days_from_now(8)}.",
            "ai_processed": True,
            "labels": ["INBOX"],
        },
        # ── Job hunting ───────────────────────────────────────────────────────
        {
            "gmail_id": "demo_job_001",
            "subject": "Thank you for interviewing at Stripe",
            "sender": "recruiting@stripe.com",
            "sender_name": "Stripe Recruiting",
            "snippet": "We've decided to move forward with other candidates at this time.",
            "body_text": (
                "Hi,\n\n"
                "Thank you for taking the time to interview with us for the Software Engineer role.\n\n"
                "After careful consideration, we've decided to move forward with other candidates "
                "whose experience more closely matches our current needs. This was a competitive "
                "process and we appreciate the time you invested.\n\n"
                "We'll keep your information on file and encourage you to apply again in the future.\n\n"
                "Best of luck,\nStripe Recruiting"
            ),
            "received_at": _days_ago(5),
            "ai_category": "worth_reading",
            "ai_summary": "Stripe declined to move forward after interview — encouraged to reapply.",
            "ai_processed": True,
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_job_002",
            "subject": "Offer Letter – Software Engineer II at Linear",
            "sender": "offers@linear.app",
            "sender_name": "Linear People Team",
            "snippet": "We're excited to offer you a position at Linear! Please review and sign by "
            + _days_from_now(5)
            + ".",
            "body_text": (
                "Hi,\n\n"
                "We're thrilled to extend an offer for the Software Engineer II role at Linear!\n\n"
                "Compensation package:\n"
                "  • Base salary: $185,000/year\n"
                "  • Equity: 0.08% (4-year vest, 1-year cliff)\n"
                "  • Signing bonus: $20,000\n"
                "  • Benefits: Full medical/dental/vision, $2,000/year L&D budget\n\n"
                "Start date: " + _days_from_now(21) + "\n\n"
                f"Please sign your offer letter by {_days_from_now(5)}:\n"
                "https://docusign.example/linear-offer-abc123\n\n"
                "We can't wait to have you on the team!\n\n"
                "— The Linear People Team"
            ),
            "received_at": _days_ago(0.6),
            "ai_category": "action_required",
            "ai_summary": f"Linear offer: SWE II, $185K + equity + $20K signing — sign by {_days_from_now(5)}.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(5),
            "action_items": [
                f"Sign Linear offer letter at docusign.example by {_days_from_now(5)}"
            ],
            "labels": ["INBOX"],
        },
        {
            "gmail_id": "demo_job_003",
            "subject": "Congrats — moving to final round – Vercel",
            "sender": "recruiting@vercel.com",
            "sender_name": "Vercel Recruiting",
            "snippet": "You've passed the technical screen. Final round interviews are next week.",
            "body_text": (
                "Hi,\n\n"
                "Congratulations — you've passed the technical screen and we'd like to "
                "move you to the final round for the Senior Frontend Engineer role!\n\n"
                "Final round format (4 hours total, remote):\n"
                "  1. System design (45 min)\n"
                "  2. Coding interview (60 min)\n"
                "  3. Cross-functional interview (45 min)\n"
                "  4. Hiring manager conversation (30 min)\n\n"
                f"Scheduling link: https://calendly.example/vercel-final (book by {_days_from_now(3)})\n\n"
                "Let us know if you have any questions!\n\n"
                "— Vercel Recruiting"
            ),
            "received_at": _days_ago(0.9),
            "ai_category": "action_required",
            "ai_summary": f"Vercel final round for Senior FE Engineer — schedule 4-hour loop by {_days_from_now(3)}.",
            "ai_processed": True,
            "deadline_extracted": _days_from_now(3),
            "action_items": [
                f"Schedule Vercel final round at calendly.example/vercel-final by {_days_from_now(3)}"
            ],
            "labels": ["INBOX"],
        },
    ]


async def seed_demo_emails(user_id: UUID, account_id: UUID) -> int:
    """Upsert demo emails for *user_id* under *account_id*.

    Idempotent — safe to call multiple times; existing rows are updated in
    place via ``on_conflict=account_id,gmail_id``.  Returns the number of
    rows written.
    """
    emails = _build_emails()
    rows = [
        {
            **email,
            "user_id": str(user_id),
            "account_id": str(account_id),
            "action_items": email.get("action_items", []),
            "is_archived": email.get("is_archived", False),
            "is_read": email.get("is_read", False),
            "is_pickup_code": email.get("is_pickup_code", False),
            "pickup_used": False,
            "labels": email.get("labels", ["INBOX"]),
        }
        for email in emails
    ]

    def _upsert() -> int:
        result = (
            get_service_client()
            .table("emails")
            .upsert(rows, on_conflict="account_id,gmail_id")
            .execute()
        )
        return len(result.data) if result.data else 0

    count = await asyncio.to_thread(_upsert)
    logger.info("seeded %d demo emails for user %s account %s", count, user_id, account_id)
    return count
