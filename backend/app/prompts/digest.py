from __future__ import annotations

DIGEST_PROMPT = """You write a daily morning briefing. Given a list of action-required
emails from the last 24 hours and upcoming deadlines in the next 7 days,
return up to 5 most-important items in priority order (deadlines soonest
first, then by recency).

Each item is one sentence ≤20 words combining the urgency reason with
the sender. Skip items that are merely informational.

Output ONLY: {"items":[{"summary":"string","source_email_id":"uuid",
"deadline":"YYYY-MM-DD"|null,"sender":"string"}]}"""
