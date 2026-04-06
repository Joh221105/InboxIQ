# InboxIQ 📬
> AI-Powered Unified Email Management App

---

## Overview
InboxIQ aggregates all your email accounts into one intelligent 
dashboard. Users set their current "life context" — job hunting, 
online shopping, school applications — and the AI automatically 
triages every incoming email by urgency, extracts deadlines and 
action items, and tracks package pickup codes.

The problem: people who manage multiple inboxes miss critical 
emails (interview invites, OA deadlines, pickup code expirations) 
because they are buried under ads and promotions. InboxIQ solves 
this by acting as an AI-powered filter that shows users only what 
actually matters — in real time, across all their accounts.

---

## Revenue Model
InboxIQ operates on a freemium SaaS model:

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/month | 1 connected inbox, basic AI triage, pickup tracker |
| **Pro** | $8/month | Unlimited inboxes, full context modes, contact tagging, deadline extraction |
| **Team** | $20/user/month | Shared inbox labels, admin dashboard, priority support |

**Additional revenue streams:**
- Annual plan discount (20% off Pro) to improve retention
- Enterprise licensing for organizations managing shared inboxes

**Market validation:** Gmail has 1.8B active users. Tools like 
Superhuman ($30/month) demonstrate strong willingness to pay for 
email productivity. InboxIQ targets a lower price point with 
broader multi-account support as its primary differentiator.

---

## Core Features
- 🔗 **Multi-inbox aggregation** — Connect Gmail & Outlook via OAuth
- 🤖 **AI email triage** — Classify emails into 🔴 Action Required / 
  🟡 Worth Reading / ⚪ Auto-Archive based on life context
- ⏰ **Deadline extraction** — AI pulls due dates from email body 
  and surfaces them as reminders
- 📦 **Package tracker** — Auto-detect pickup codes, one-tap 
  mark as used
- 🏷️ **Contact tagging** — Flag professors, friends, and recruiters 
  for instant highlight
- 📊 **Daily digest dashboard** — Morning briefing of everything 
  that needs attention today

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 + Tailwind CSS + shadcn/ui |
| Backend | FastAPI (Python) |
| AI | OpenAI GPT-4o |
| Email APIs | Gmail API + Microsoft Graph API (OAuth 2.0) |
| Database | PostgreSQL via Supabase |
| Auth | Supabase Auth |
| Deployment | Vercel (frontend) + Railway (backend) |

---

## Team
| Role | Name | Responsibilities |
|------|------|-----------------|
| Proposer (Client) | Ting Li | Spec, issue creation, PR review, acceptance testing, Demo Day pitch |
| Developer | John Huang | Architecture, implementation, testing, PR submission |
| Development Fee | 50 GIX Bucks | Paid on final delivery |

---

## Repository Structure
```
inboxiq/
├── frontend/          # Next.js app
├── backend/           # FastAPI app
├── SPEC.md            # Full project specification
├── ARCHITECTURE.md    # Developer's architecture document (by John Huang)
├── CLAUDE.md          # AI-assisted development config
├── .cursorrules       # Cursor rules for agentic engineering
└── README.md          # This file
```

---

## Branch Protection Rules
- `main` branch requires **at least 1 approving review** before merge
- All features must be submitted via Pull Request referencing a GitHub Issue
- Direct pushes to `main` are disabled
- Developer must respond to all review comments within **48 hours**
- Proposer must review all PRs within **48 hours**

---

## Development Timeline (2 Weeks)

| Milestone | Deadline | Required Progress | Acceptance Gate |
|-----------|----------|-------------------|-----------------|
| ✅ **Check-in 1** | End of Week 1, Day 3 | OAuth login working for Gmail; emails fetched and stored in DB; project deployed to staging URL; ARCHITECTURE.md submitted | Proposer reviews Architecture PR within 48 hours |
| ✅ **Check-in 2** | End of Week 1, Day 6 | AI triage pipeline working (3-category classification + summary); context mode switcher functional; unified inbox page live on staging | Proposer conducts acceptance test on inbox triage accuracy |
| ✅ **Check-in 3** | End of Week 2, Day 3 | Package tracker complete with auto-detection and mark-as-used; deadline extraction working; contact tagging functional; all MVP issues closed | Proposer files bug reports; developer resolves within 48 hours |
| 🏁 **Final Delivery** | End of Week 2 | All MVP features polished and deployed to production URL; README updated; tests passing; demo-ready | Final acceptance test by proposer; GIX Bucks paid on approval |

---

## GitHub Issues
The full project is decomposed into the following issues. 
Each PR must reference its corresponding issue.

| # | Issue | Epic |
|---|-------|------|
| 1 | Project Setup & Repo Scaffolding | `setup` |
| 2 | Database Schema & Supabase Auth | `setup` |
| 3 | Gmail OAuth & Email Sync Pipeline | `auth` |
| 4 | AI Triage Pipeline (classify + summarize + extract) | `ai` |
| 5 | Unified Inbox Page | `inbox` |
| 6 | Dashboard & Daily Digest | `dashboard` |
| 7 | Package Tracker Page | `tracker` |
| 8 | Contact Tags & Settings Pages | `contacts` |

---

## Acceptance Criteria Summary
Each issue has its own detailed acceptance criteria. 
High-level gates for final delivery:

- [ ] User can connect at least 1 Gmail account via OAuth
- [ ] All emails displayed in unified inbox with triage badges
- [ ] Switching context mode visibly changes triage results
- [ ] AI summary visible on every email card
- [ ] At least 1 deadline correctly extracted from a real email
- [ ] Pickup code auto-detected from a real Amazon/FedEx email
- [ ] Mark as Used archives the source email
- [ ] Contact tag visually highlights emails from tagged sender
- [ ] Daily digest shows on dashboard home
- [ ] App deployed to public production URL
- [ ] No critical bugs open at time of final delivery

---

## Contract Terms
Per course requirements, both parties commit to:

**Proposer (Ting Li):**
- Review all PRs within 48 hours
- Provide specific, actionable written feedback on every review
- Respond to developer questions within 48 hours
- File bug reports with reproduction steps and screenshots

**Developer (John Huang):**
- Submit at least one PR per 2-week period
- Respond to all review comments within 48 hours
- Keep proposer informed of any blockers immediately
- Use agentic engineering tools (Cursor / Claude Code) for all implementation

Disputes are resolved by creating a GitHub Issue tagged 
`escalation` for instructor review.

---

## Demo Day
**Proposer presents:**
- The problem and target user
- Revenue model and market opportunity
- Development story: what was built, what feedback was given, 
  what changed through the process

**Developer presents:**
- System architecture (C4 diagram from ARCHITECTURE.md)
- Agentic engineering approach and AI tooling used
- Key technical decisions and tradeoffs

---

## Getting Started (for Developer)
```bash
# Clone the repo
git clone https://github.com/[your-username]/inboxiq.git

# Frontend setup
cd frontend
npm install
cp .env.example .env.local
npm run dev

# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

**Required environment variables:**
```
OPENAI_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
```