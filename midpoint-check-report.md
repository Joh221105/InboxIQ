---
title: "InboxIQ — Mid-Point Check Report"
author: "Ting Li (Proposer)"
date: "May 4, 2026"
geometry: "margin=2.5cm"
fontsize: 11pt
colorlinks: true
---

## Project Overview

**Project:** InboxIQ — AI-Powered Unified Email Management App  
**Developer:** John Huang  
**Reviewer:** Ting Li (Proposer)  
**Check Date:** May 4, 2026  
**Sprint Start:** April 6, 2026 (2-week timeline)

InboxIQ aggregates email accounts into one intelligent dashboard. Users set a "life context" (Job Hunting, Online Shopping, School Applications) and the AI automatically triages emails by urgency, extracts deadlines, and tracks package pickup codes.

---

## 1. Milestone Status

| Milestone | Deadline | Status | Verdict |
|-----------|----------|--------|---------|
| Check-in 1 | Week 1, Day 3 | Gmail OAuth merged (PR \#11), ARCHITECTURE.md merged (PR \#2). Emails **not** stored in DB — fetched live only. No staging deployment confirmed. | **Partial** |
| Check-in 2 | Week 1, Day 6 | No AI triage. No context mode switcher. No `/inbox` page. OpenAI not integrated. | **Not met ❌** |
| Check-in 3 | Week 2, Day 3 | Package tracker missing. Dashboard missing. DB schema incomplete. All feature issues (\#4–\#9) still open. | **Not met ❌** |
| Final Delivery | Week 2 | 6 blocker bugs filed. Most MVP features have zero implementation. | **At risk ❌** |

---

## 2. Acceptance Criteria Results

**Score: 1 / 11 criteria met.**

| Acceptance Criterion | Result | Evidence |
|----------------------|--------|---------|
| User can connect ≥1 Gmail account via OAuth | ✅ Pass | `inbox-home.tsx` + `gmail_auth.py` |
| All emails displayed in unified inbox with triage badges | ❌ Fail | No triage badges exist. Cards show raw snippet only. Bug \#12 |
| Switching context mode visibly changes triage results | ❌ Fail | No context switcher in UI anywhere. Bug \#13 |
| AI summary visible on every email card | ❌ Fail | No OpenAI integration; email body never fetched. Bugs \#12, \#14 |
| At least 1 deadline correctly extracted from a real email | ❌ Fail | Not implemented. No extraction logic exists. |
| Pickup code auto-detected from a real Amazon/FedEx email | ❌ Fail | `/packages` page does not exist. Bug \#15 |
| Mark as Used archives the source email | ❌ Fail | Not implemented. |
| Contact tag visually highlights emails from tagged sender | ❌ Fail | Not implemented. |
| Daily digest shows on dashboard home | ❌ Fail | App root shows basic email preview, not the dashboard. Bug \#16 |
| App deployed to public production URL | ❌ Fail | Issue \#10 still open. No URL provided. |
| No critical bugs open at time of final delivery | ❌ Fail | 6 blocker bugs filed (issues \#12–\#17). |

---

## 3. What Is Working

- **Supabase magic-link authentication** — `/login` page functional; session handling and middleware working correctly.
- **Gmail OAuth 2.0 flow** — User can connect a Gmail account; access/refresh tokens stored server-side in `connected_accounts` table.
- **Basic email metadata fetch** — `GET /emails` returns up to 15 messages with subject, sender, date, and raw Gmail snippet.

---

## 4. Bug Reports Filed

All 6 bugs filed on GitHub using `bug-report-template.md` with reproduction steps and code evidence.

| \# | Title | Feature | Severity |
|----|-------|---------|----------|
| \#12 | AI triage badges and summaries completely missing from email cards | \#5 | **Blocker** |
| \#13 | Context mode switcher absent from UI | \#5 | **Blocker** |
| \#14 | Email body never fetched; no OpenAI client in codebase | \#5, \#6, \#8 | **Blocker** |
| \#15 | Package tracker page (`/packages`) does not exist | \#8 | **Blocker** |
| \#16 | App root renders raw email preview, not the dashboard | \#9 | **Blocker** |
| \#17 | `emails` and `contact_tags` DB tables never created | \#4–\#8 | **Blocker** |

All bugs are live at: `https://github.com/GIX-Luyao/final-project-codebase-Ting1016-git/issues`

---

## 5. Root Cause Analysis

Two foundational problems are blocking all AI features:

**Problem 1 — Email body is never fetched.**  
`backend/app/gmail_fetch.py` calls the Gmail API with `format="metadata"`, which returns headers only — no body content. All AI features (triage, summarization, deadline extraction, pickup code detection) require the full email body. The raw Gmail `snippet` field (100–200 characters) is not a substitute.

```python
# gmail_fetch.py lines 76-83 — fetches NO body
detail = service.users().messages().get(
    userId="me", id=mid,
    format="metadata",      # ← headers only, no content
    metadataHeaders=["Subject", "From", "Date"]
).execute()
```

**Problem 2 — OpenAI is not integrated.**  
The `openai` package is absent from `backend/requirements.txt`. There is no AI client, no prompt templates, and no triage logic anywhere in the codebase. Without fixing both problems above, no AI feature can be built or tested.

---

## 6. Open GitHub Issues

| Issue | Title | Status |
|-------|-------|--------|
| \#4 | Build unified inbox view with multi-account email aggregation | Open |
| \#5 | Implement AI email triage with life context mode | Open |
| \#6 | AI deadline extraction and reminder display | Open |
| \#7 | Contact tagging system (Professor / Friend / Recruiter) | Open |
| \#8 | Package pickup code auto-detection and tracker UI | Open |
| \#9 | Dashboard home page with daily AI digest | Open |
| \#10 | Production deployment setup (Vercel + Railway) | Open |

---

## 7. Is the Developer On Track?

**No.** At the Check-in 3 deadline, 7 of 8 feature issues remain open and 10 of 11 acceptance criteria are unmet. The only working feature beyond basic auth is a minimal email list preview. The entire AI layer — the core value proposition of InboxIQ — has not been started.

Per contract terms, the developer must **respond to all 6 bug reports within 48 hours**. Final GIX Bucks payment is contingent on all acceptance criteria being met before Demo Day.

---

## 8. Deliverables Completed

- [x] `README.md` updated with mid-point status and pushed to `main`
- [x] 6 bug issues filed on GitHub (\#12–\#17) with reproduction steps and code evidence
- [x] Acceptance criteria evaluated against actual implementation
- [x] Developer on-track assessment completed
