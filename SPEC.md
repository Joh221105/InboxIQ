# InboxIQ — Project Specification

## Overview
InboxIQ is an AI-powered unified email management web app that 
aggregates multiple email accounts into a single intelligent 
dashboard. Users set their current "life context" — such as 
job hunting, online shopping, or school applications — and the 
AI automatically triages every incoming email by urgency, 
extracts deadlines and action items, and tracks package pickup 
codes. The goal is to eliminate inbox anxiety and ensure users 
never miss what matters.

The app is deployed to a public URL with user authentication 
handled via Supabase.

---

## Team
| Role | Name |
|------|------|
| Client / Proposer | Mengting Li |
| Developer | John Huang |
| Agreed Development Fee | 40 GIX Bucks |

---

## User Stories

### Epic 1: Multi-Inbox Setup
- As a user, I want to connect multiple Gmail and Outlook 
  accounts via OAuth so that I never have to log into each 
  inbox separately.
- As a user, I want to see all emails from all accounts in 
  one unified inbox view so that I can manage everything 
  in one place.
- As a user, I want the app to remember which email address 
  is registered to which service so that I always know which 
  account to check when I need to log into something.

### Epic 2: AI Email Triage
- As a user, I want to set my current "life context" 
  (Job Hunting / Online Shopping / School Application / Daily) 
  so that the AI knows which types of emails are most 
  important right now.
- As a user, I want every email automatically classified into 
  🔴 Action Required / 🟡 Worth Reading / ⚪ Auto-Archive so 
  that I only see what actually needs my attention.
- As a user, I want the AI to extract deadlines and action 
  items from email content (e.g. "Complete OA by Nov 15, 
  11:59 PM") and display them as reminders so that I never 
  miss a deadline buried in an email.
- As a user, I want the AI to adapt its triage logic when 
  I switch contexts so that the same email can be urgent 
  in one context and ignorable in another.

### Epic 3: Smart Summaries & Notifications
- As a user, I want a one-line AI summary on every email 
  card so that I can understand the email without opening it.
- As a user, I want a daily digest at the top of my dashboard 
  summarizing today's action items across all inboxes so that 
  I start each day knowing exactly what needs attention.
- As a user, I want emails from tagged contacts (professors, 
  friends, recruiters) to always be highlighted regardless of 
  the current context so that I never miss a personal or 
  important message.

### Epic 4: Package & Pickup Code Tracker
- As a user, I want the app to automatically detect package 
  pickup code emails (Amazon Locker, FedEx, UPS) so that all 
  active codes appear in one place without manual searching.
- As a user, I want a card-based view of all active pickup 
  codes showing the retailer name, code, and expiry date so 
  that I can find any code instantly.
- As a user, I want to mark a pickup code as "Used" with one 
  tap so that the email is automatically archived and I never 
  confuse used and unused codes.

### Epic 5: Contact Tagging
- As a user, I want to label any email address or domain as 
  "Professor", "Friend", "Recruiter", or a custom tag so that 
  emails from those contacts are always visually distinguished.
- As a user, I want to receive a special notification when a 
  tagged contact sends me an email so that I never miss a 
  message from someone important.

---

## Pages & UI Detail

### Page 1: Dashboard (/)
The main home screen users return to every day.

**Layout:**
- Header: App name, account icon, context mode badge
- Daily AI Digest Banner: Top 3–5 action-required emails 
  summarized in one line each, with sender and deadline 
  if detected
- Upcoming Deadlines Panel: Chronological list of extracted 
  deadlines across all inboxes
- Active Pickup Codes Widget: Compact card strip showing 
  all unclaimed codes. Each card shows retailer, code, 
  and expiry. One-tap "Mark as Used" button.
- Context Mode Switcher: Pill buttons — Job Hunting / 
  Shopping / School Application / Daily

**Behavior:**
- Digest updates every time the user opens the app
- Marking a pickup code as Used archives the source email 
  and removes the card from the widget
- Switching context mode immediately re-runs triage on 
  the last 100 unread emails

---

### Page 2: Unified Inbox (/inbox)
All emails from all connected accounts in one scrollable view.

**Layout:**
- Filter Tabs: All / 🔴 Action Required / 🟡 Worth Reading / 
  ⚪ Auto-Archived
- Each Email Card shows:
  - Sender name + contact tag badge if applicable
  - Subject line
  - One-line AI summary
  - Extracted deadline badge if present (e.g. "Due Nov 15")
  - Source account indicator (color-coded dot)
  - Triage category badge
- Search bar with keyword and sender filter

**Behavior:**
- Emails sorted by triage priority within each tab, then 
  by recency
- Clicking an email opens it inline or in a side panel 
  without leaving the inbox
- Auto-Archived emails accessible but collapsed by default
- Contact tag badges clickable — opens tag management for 
  that sender

---

### Page 3: Package Tracker (/packages)
A dedicated view for all pickup codes and delivery emails.

**Layout:**
- Active Codes section: Card grid, each card shows:
  - Retailer name and logo (if detectable)
  - Pickup code in large, readable font
  - Locker location if present in email
  - Expiry date if present
  - "Mark as Used" button
- Used / Archived section: Collapsed list of past codes 
  with timestamp of when they were marked used

**Behavior:**
- AI scans all connected inboxes for pickup code patterns 
  on initial setup and on each new email sync
- Marking a code as Used archives the source email and 
  moves the card to the archived section
- If an expiry date is detected and the code is within 
  24 hours of expiring, an expiry warning badge appears

---

### Page 4: Contact Tags (/contacts)
Manage labeled contacts and see their email history.

**Layout:**
- Tag list: Professor / Friend / Recruiter / Custom
- Each tag shows all associated email addresses or domains
- "Add Contact" button: enter email address or domain, 
  assign a tag
- Per-contact email history: all emails from that contact 
  across all inboxes

**Behavior:**
- Tags applied retroactively to all existing emails on save
- Domain-level tagging (e.g. @uw.edu → Professor) supported
- Custom tags creatable with user-defined label and color

---

### Page 5: Settings (/settings)
Account and app configuration.

**Sections:**
- Connected Accounts: List of all linked inboxes with 
  disconnect button per account. "Add Account" button.
- Context Mode: Default context on app open
- Notification Preferences: Which tags trigger special 
  notifications
- Privacy: Data retention settings, option to delete all 
  stored email data

---

## Navigation
```
/            — Dashboard (home)
/inbox       — Unified Inbox
/packages    — Package Tracker
/contacts    — Contact Tags
/settings    — Settings & Connected Accounts
```

---

## Design Requirements
The app should feel like a calm, focused productivity tool — 
not an email client that adds clutter. Reference Superhuman 
and Linear for visual tone.

**General Principles:**
- Clean, minimal UI with generous whitespace
- Each connected account has a distinct color used 
  consistently on email cards and filter indicators
- Smooth transitions and micro-animations throughout
- Responsive for desktop and tablet

**Triage Color System:**
- 🔴 Action Required: Red left border on email card
- 🟡 Worth Reading: Yellow left border
- ⚪ Auto-Archive: No border, reduced opacity

**Dashboard Specifics:**
- Daily Digest Banner should feel like a morning briefing — 
  clean card, not an alert
- Pickup Code cards should be bold and scannable — 
  the code itself in large monospace font
- Context mode switcher always visible, never buried in 
  settings

---

## Database Schema

### users
| Column | Type | Description |
|--------|------|-------------|
| id | UUID / PK | Primary key |
| email | TEXT (unique) | User email via Supabase Auth |
| default_context | TEXT | Job Hunting, Shopping, School, Daily |
| created_at | TIMESTAMP | Account creation date |

### connected_accounts
| Column | Type | Description |
|--------|------|-------------|
| id | UUID / PK | Primary key |
| user_id | FK → users | Owning user |
| email_address | TEXT | The connected email address |
| provider | TEXT | gmail or outlook |
| oauth_token | JSONB | OAuth access + refresh token |
| color | TEXT | Hex color for this account |
| created_at | TIMESTAMP | When account was connected |

### emails
| Column | Type | Description |
|--------|------|-------------|
| id | UUID / PK | Primary key |
| account_id | FK → connected_accounts | Source inbox |
| external_id | TEXT | Provider's message ID |
| sender_email | TEXT | From address |
| subject | TEXT | Email subject |
| received_at | TIMESTAMP | When email was received |
| ai_summary | TEXT | One-line AI summary |
| triage_category | TEXT | action_required, worth_reading, auto_archive |
| deadline_extracted | DATE (nullable) | Deadline pulled from body |
| is_pickup_code | BOOLEAN | Whether a pickup code was detected |
| pickup_code | TEXT (nullable) | Extracted code value |
| pickup_expiry | DATE (nullable) | Expiry date if detected |
| pickup_used | BOOLEAN | Whether marked as used |
| is_archived | BOOLEAN | Whether archived |

### contact_tags
| Column | Type | Description |
|--------|------|-------------|
| id | UUID / PK | Primary key |
| user_id | FK → users | Owning user |
| identifier | TEXT | Email address or @domain |
| tag | TEXT | professor, friend, recruiter, custom |
| custom_label | TEXT (nullable) | Label if tag is custom |
| color | TEXT | Display color for badge |
| created_at | TIMESTAMP | When tag was created |

---

## AI Architecture
**LLM:** OpenAI GPT-4o via OpenAI API

**Used for:**
- Email triage classification (category + confidence score)
- One-line summary generation per email
- Deadline and action item extraction from email body
- Pickup code detection and parsing
- Daily digest generation

**Context strategy:** Each AI call is self-contained. The 
email subject, sender, and body are passed per request. 
No cross-session AI memory. Triage logic is re-run when 
the user switches context mode.

**Prompt stability:** Static system prompts per call type 
to maximize performance consistency.

**Edge cases:**
- Email body too long: truncate to first 2000 tokens, 
  note truncation in summary
- Non-English email: detect language, summarize in English
- No body content (image-only email): flag as 
  "Content not readable — manual review suggested"
- API error during triage: display email without summary, 
  show "AI unavailable" badge, retry on next sync

---

## AI Triage Logic by Context

| Context Mode | Action Required | Worth Reading | Auto-Archive |
|---|---|---|---|
| Job Hunting | Interview invite, OA deadline, offer letter, rejection | Application confirmation, recruiter outreach, job recommendations | Job board newsletters, LinkedIn digests |
| Shopping | Pickup code, delivery exception, return deadline | Order confirmation, shipping update | Promotional emails, sale announcements |
| School Application | Admission result, document request, interview invite | Application status update, scholarship info | University newsletters, campus event emails |
| Daily | Emails from tagged contacts, bills due, account alerts | Service updates, receipts | Ads, newsletters, social notifications |

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

## Must-Have Features
- OAuth connection for at least Gmail
- Unified inbox view with AI triage (3-category system)
- Context mode switcher with dynamic re-triage
- One-line AI summary per email
- Deadline extraction and display
- Package pickup code auto-detection and tracker
- Contact tagging with visual highlight
- Daily dashboard digest

---

## Out of Scope (V2)
- Account × App mapping (AI scans "Welcome to XXX" emails 
  to build a registry of which email is registered where)
- One-click unsubscribe manager
- Mobile native app
- Push or email notifications
- Outlook support (Gmail-only for MVP)

---

## GitHub Issues Breakdown

**Issue 1: Project Setup & Repo Scaffolding**
Set up Next.js frontend and FastAPI backend. Configure 
environment variables for OpenAI API, Supabase, Gmail OAuth. 
Establish folder structure. Deploy skeleton to Vercel + Railway.

**Issue 2: Database Schema & Supabase Auth**
Create all tables (users, connected_accounts, emails, 
contact_tags). Set up Supabase Auth. Implement row-level 
security policies. Set up goal color assignment for accounts.

**Issue 3: Gmail OAuth & Email Sync**
Implement Gmail OAuth 2.0 flow. Build email fetch and sync 
pipeline. Store raw email data in the emails table. Handle 
token refresh and sync failure recovery.

**Issue 4: AI Triage Pipeline**
Integrate OpenAI GPT-4o for per-email triage classification, 
summary generation, deadline extraction, and pickup code 
detection. Implement context-aware prompt switching. Handle 
edge cases: image-only emails, non-English content, API errors.

**Issue 5: Unified Inbox Page**
Build the /inbox page with filter tabs, email card components, 
search bar, and inline email preview. Implement real-time 
triage badge rendering and contact tag badges.

**Issue 6: Dashboard & Daily Digest**
Build the / dashboard with daily digest banner, deadlines 
panel, pickup code widget, and context mode switcher. 
Implement digest generation logic from triaged emails.

**Issue 7: Package Tracker Page**
Build the /packages page with card grid for active codes 
and archived list. Implement "Mark as Used" flow including 
email archival. Surface expiry warnings.

**Issue 8: Contact Tags & Settings**
Build the /contacts page and /settings page. Implement 
contact and domain tagging with retroactive application 
to existing emails. Build connected accounts management UI.

---

## Labels
| Label | Value |
|-------|-------|
| Stack | `stack:negotiable` |
| AI | `ai:yes` |
| Complexity | `complexity:ambitious` |