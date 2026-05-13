from __future__ import annotations

DEADLINE_PROMPT = """You extract deadlines from emails. The user message will include the
email's received_at timestamp; resolve relative dates ("by next Friday",
"in 3 days") against it. If multiple deadlines exist, return the soonest
ACTION-REQUIRED one (not "auto-renewal in 1 year"). If no deadline,
return null fields.

Output ONLY this JSON:
{"deadline":"YYYY-MM-DD"|null, "deadline_text":"verbatim phrase from
email"|null, "confidence":"high"|"medium"|"low"}"""

ACTION_ITEMS_PROMPT = """You extract action items from emails — specific things the user must
DO. Imperative phrasing, 80 chars max each, max 5 items. Skip
informational statements.

Output ONLY: {"action_items": ["string", ...]}"""

PICKUP_CODE_PROMPT = """You extract pickup codes from package delivery emails. Distinguish
TRUE pickup codes (Amazon Locker / Hub Counter / Hub Locker, FedEx hold,
UPS Access Point, USPS held mail, DHL ServicePoint) from "informed
delivery" notifications which preview mail but have no pickup code.

If no genuine pickup code is found, return all fields null.

Output ONLY: {"pickup_code":"string"|null, "pickup_expiry":"YYYY-MM-DD"|null,
"retailer":"Amazon"|"FedEx"|"UPS"|"USPS"|"DHL"|"Other"|null,
"locker_location":"string"|null}"""
