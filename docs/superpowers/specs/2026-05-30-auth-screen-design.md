# Auth Screen Design

**Date:** 2026-05-30
**Scope:** Sign-in / sign-up screen for InboxIQ (email + password, single page with tab toggle)

---

## 1. Routing & Layout

Introduce Next.js route groups to fix the current bug where `AppNav` renders on auth pages.

### File moves

| From | To | URL |
|---|---|---|
| `app/auth/sign-in/page.tsx` | `app/(auth)/auth/sign-in/page.tsx` | `/auth/sign-in` (unchanged) |
| `app/auth/callback/route.ts` | `app/(auth)/auth/callback/route.ts` | `/auth/callback` (unchanged) |
| `app/page.tsx` | `app/(app)/page.tsx` | `/` (unchanged) |
| `app/inbox/page.tsx` | `app/(app)/inbox/page.tsx` | `/inbox` (unchanged) |
| `app/settings/page.tsx` | `app/(app)/settings/page.tsx` | `/settings` (unchanged) |
| `app/contacts/page.tsx` | `app/(app)/contacts/page.tsx` | `/contacts` (unchanged) |
| `app/packages/page.tsx` | `app/(app)/packages/page.tsx` | `/packages` (unchanged) |
| `app/error.tsx` | `app/(app)/error.tsx` | — |
| `app/not-found.tsx` | `app/(app)/not-found.tsx` | — |

### New layout files

**`app/layout.tsx`** (modified — remove AppNav and `flex h-screen` from body, keep only structural shell):
```tsx
<html><body className="antialiased"><Providers>{children}</Providers><Toaster /></body></html>
```

**`app/(app)/layout.tsx`** (new — authenticated shell with nav, takes over the `flex h-screen` that was on root body):
```tsx
<div className="flex h-screen">
  <AppNav />
  <main className="flex-1 overflow-auto">{children}</main>
</div>
```

**`app/(auth)/layout.tsx`** (new — full-screen centering, no nav):
```tsx
<div className="flex min-h-screen items-center justify-center bg-background">
  {children}
</div>
```

---

## 2. Page Component

**File:** `app/(auth)/auth/sign-in/page.tsx`

A shadcn `Card` (max-width `sm`, full-width on mobile) centered by the `(auth)` layout.

### Card structure

```
┌─────────────────────────────┐
│  InboxIQ                    │
│  AI-powered email management│
│                             │
│  [Sign in]  [Sign up]       │  ← shadcn Tabs
│ ─────────────────────────── │
│  Email                      │
│  [________________]         │
│                             │
│  Password                   │
│  [________________]         │
│                             │
│  Forgot password?           │  ← link, swaps card to reset view
│                             │
│  [     Sign in     ]        │  ← full-width primary Button
│                             │
│  (error message if any)     │
└─────────────────────────────┘
```

Sign up tab replaces the password field with two fields (Password + Confirm password) and the button label changes to "Create account". No "Forgot password?" link on sign-up tab.

### Forgot password view

Clicking "Forgot password?" replaces the tab content with:
- Back arrow link ("← Back to sign in")
- Email field
- "Send reset link" button
- On success: "Check your email for a reset link." confirmation text (button disappears)

This is inline state — no separate route.

### Loading & error states

- Button is `disabled` and label changes to "Signing in…" / "Creating account…" / "Sending…" during in-flight requests.
- Errors appear as `<p className="text-sm text-destructive text-center">` below the button.
- Confirm password mismatch is caught client-side before the Supabase call and shown as the same error style.

---

## 3. Supabase Calls

All calls use `createBrowserSupabaseClient()` from `@/lib/supabase/client`.

| Action | Call | On success | On error |
|---|---|---|---|
| Sign in | `supabase.auth.signInWithPassword({ email, password })` | `router.push("/")` | Show error |
| Sign up | `supabase.auth.signUp({ email, password })` | `router.push("/")` | Show error |
| Forgot password | `supabase.auth.resetPasswordForEmail(email, { redirectTo: origin + "/auth/callback" })` | Show confirmation text | Show error |

**Note:** Supabase email confirmation must be disabled in the Supabase dashboard (Authentication → Settings → "Enable email confirmations" off) for sign-up to redirect immediately to `/`.

The existing `app/(auth)/auth/callback/route.ts` handles the `code` → session exchange for both magic links and password reset redirects — no changes needed.

---

## 4. Out of Scope

- Google OAuth (not requested)
- Password strength meter
- Rate limiting UI (handled server-side by Supabase)
- "Remember me" checkbox
