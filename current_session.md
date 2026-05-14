# Current Session - Issue 6 Dashboard & Daily Digest

- Branch: `issue-6-dashboard`
- Implemented backend `/emails` deadline filtering and ordering:
  - `has_deadline=true`
  - `deadline_after=YYYY-MM-DD`
  - `deadline_before=YYYY-MM-DD`
  - `order=deadline_asc` with deadline ascending and received date descending
- Confirmed and extended `/digest/today` response shape:
  - `{ generated_at, items, degraded, context }`
  - empty digest returns `{ degraded: false, items: [] }`
- Implemented dashboard frontend:
  - context switcher pills with optimistic context updates and retriage polling
  - daily digest banner with calm empty state, degraded fallback note, deadline pills, and inbox deep links
  - upcoming deadlines panel using the new `/emails` filters
  - pickup codes strip reusing active pickup-code data
  - zero-account empty dashboard linking to settings
  - `/inbox?email_id=...` opens the matching detail panel when loaded
- Added tests:
  - backend email router deadline filters/order coverage
  - digest service context-shape-safe tests
  - dashboard digest banner component tests
  - context switch mutation polling/rollback tests
  - dashboard Playwright happy path
- Screenshot:
  - `plans/issue-6-screenshot.png`

Verification run:

- `cd backend && pytest` -> 130 passed, 1 skipped
- `cd frontend && npm test` -> 36 passed
- `cd frontend && npm run build` -> passed
- `cd frontend && npx playwright test tests/e2e/dashboard.spec.ts` -> 1 passed
