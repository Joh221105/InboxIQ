# Auth Screen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the bare-bones magic-link sign-in page with a polished email+password sign-in/sign-up screen using shadcn components, and fix the layout so AppNav is hidden on auth pages.

**Architecture:** Introduce Next.js App Router route groups — `(app)` for authenticated pages (has AppNav) and `(auth)` for auth pages (no nav). The sign-in page at `/auth/sign-in` becomes a single card with Tabs toggling between Sign In and Sign Up. All Supabase auth calls use `createBrowserSupabaseClient`.

**Tech Stack:** Next.js 14 App Router, shadcn/ui (Card, Tabs, Input, Label, Button), Supabase JS v2, Vitest + @testing-library/react.

---

## File Map

| Action | Path | Purpose |
|---|---|---|
| Modify | `frontend/app/layout.tsx` | Remove AppNav + `flex h-screen` from body |
| Create | `frontend/app/(app)/layout.tsx` | Authenticated shell — AppNav + `flex h-screen` |
| Create | `frontend/app/(auth)/layout.tsx` | Auth shell — full-screen centering, no nav |
| `git mv` | `frontend/app/page.tsx` → `frontend/app/(app)/page.tsx` | Dashboard |
| `git mv` | `frontend/app/inbox/page.tsx` → `frontend/app/(app)/inbox/page.tsx` | Inbox |
| `git mv` | `frontend/app/settings/page.tsx` → `frontend/app/(app)/settings/page.tsx` | Settings |
| `git mv` | `frontend/app/contacts/page.tsx` → `frontend/app/(app)/contacts/page.tsx` | Contacts |
| `git mv` | `frontend/app/packages/page.tsx` → `frontend/app/(app)/packages/page.tsx` | Packages |
| `git mv` | `frontend/app/error.tsx` → `frontend/app/(app)/error.tsx` | App error boundary |
| `git mv` | `frontend/app/not-found.tsx` → `frontend/app/(app)/not-found.tsx` | 404 page |
| `git mv` | `frontend/app/auth/sign-in/page.tsx` → `frontend/app/(auth)/auth/sign-in/page.tsx` | New sign-in page (rewritten) |
| `git mv` | `frontend/app/auth/callback/route.ts` → `frontend/app/(auth)/auth/callback/route.ts` | Unchanged |
| Create | `frontend/components/ui/tabs.tsx` | shadcn Tabs component (via CLI) |
| Create | `frontend/tests/auth/sign-in.test.tsx` | Vitest component tests |

---

## Task 1: Add the Tabs shadcn component

**Files:**
- Create: `frontend/components/ui/tabs.tsx`

- [ ] **Step 1: Run shadcn CLI to add Tabs**

From the `frontend/` directory:
```bash
npx shadcn@latest add tabs
```

- [ ] **Step 2: Verify the file was created**

```bash
ls frontend/components/ui/tabs.tsx
```
Expected: file exists with `TabsList`, `TabsTrigger`, `TabsContent` exports.

- [ ] **Step 3: Commit**

```bash
git add frontend/components/ui/tabs.tsx
git commit -m "feat(auth): add shadcn Tabs component"
```

---

## Task 2: Restructure layouts with route groups

**Files:**
- Modify: `frontend/app/layout.tsx`
- Create: `frontend/app/(app)/layout.tsx`
- Create: `frontend/app/(auth)/layout.tsx`
- Move (git mv): all app pages and auth files as listed in File Map

- [ ] **Step 1: Create the `(app)` and `(auth)` directories and move files**

Run each `git mv` from the `frontend/` directory:
```bash
mkdir -p app/\(app\)/inbox app/\(app\)/settings app/\(app\)/contacts app/\(app\)/packages
mkdir -p app/\(auth\)/auth/sign-in app/\(auth\)/auth/callback
git mv app/page.tsx app/\(app\)/page.tsx
git mv app/inbox/page.tsx app/\(app\)/inbox/page.tsx
git mv app/settings/page.tsx app/\(app\)/settings/page.tsx
git mv app/contacts/page.tsx app/\(app\)/contacts/page.tsx
git mv app/packages/page.tsx app/\(app\)/packages/page.tsx
git mv app/error.tsx app/\(app\)/error.tsx
git mv app/not-found.tsx app/\(app\)/not-found.tsx
git mv app/auth/sign-in/page.tsx app/\(auth\)/auth/sign-in/page.tsx
git mv app/auth/callback/route.ts app/\(auth\)/auth/callback/route.ts
```

- [ ] **Step 2: Remove now-empty directories**

```bash
rmdir app/inbox app/settings app/contacts app/packages app/auth/sign-in app/auth/callback app/auth 2>/dev/null; true
```

- [ ] **Step 3: Create `app/(app)/layout.tsx`**

```tsx
import { AppNav } from "@/components/app-nav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <AppNav />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
```

- [ ] **Step 4: Create `app/(auth)/layout.tsx`**

```tsx
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      {children}
    </div>
  );
}
```

- [ ] **Step 5: Modify `app/layout.tsx` — remove AppNav and `flex h-screen`**

Replace the entire file with:
```tsx
import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";
import { cn } from "@/lib/utils";
import { Providers } from "@/components/providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "InboxIQ",
  description: "AI-powered unified email — connect Gmail and triage your inbox",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("font-sans", inter.variable)}>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <Providers>
          {children}
          <Toaster richColors position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
```

- [ ] **Step 6: Verify TypeScript compiles with no errors**

```bash
cd frontend && npx tsc --noEmit
```
Expected: no output (clean).

- [ ] **Step 7: Commit**

```bash
git add app/\(app\)/ app/\(auth\)/ app/layout.tsx
git commit -m "feat(auth): restructure layouts with route groups, suppress nav on auth pages"
```

---

## Task 3: Write sign-in page tests (failing)

**Files:**
- Create: `frontend/tests/auth/sign-in.test.tsx`

- [ ] **Step 1: Create the test file**

```tsx
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SignInPage from "@/app/(auth)/auth/sign-in/page";

const mockSignInWithPassword = vi.fn();
const mockSignUp = vi.fn();
const mockResetPasswordForEmail = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createBrowserSupabaseClient: () => ({
    auth: {
      signInWithPassword: mockSignInWithPassword,
      signUp: mockSignUp,
      resetPasswordForEmail: mockResetPasswordForEmail,
    },
  }),
}));

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

describe("SignInPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders sign in tab with email and password fields by default", () => {
    render(<SignInPage />);
    expect(screen.getByRole("tab", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Sign up" })).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
  });

  it("calls signInWithPassword and redirects to / on success", async () => {
    mockSignInWithPassword.mockResolvedValueOnce({ error: null });
    render(<SignInPage />);

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(mockSignInWithPassword).toHaveBeenCalledWith({
        email: "user@example.com",
        password: "password123",
      });
      expect(mockPush).toHaveBeenCalledWith("/");
    });
  });

  it("shows Supabase error message when sign in fails", async () => {
    mockSignInWithPassword.mockResolvedValueOnce({
      error: { message: "Invalid login credentials" },
    });
    render(<SignInPage />);

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "user@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "wrongpass" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText("Invalid login credentials")).toBeInTheDocument();
    });
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("shows error without calling Supabase when sign up passwords do not match", async () => {
    render(<SignInPage />);
    fireEvent.click(screen.getByRole("tab", { name: "Sign up" }));

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "new@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "different" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(screen.getByText("Passwords do not match.")).toBeInTheDocument();
    expect(mockSignUp).not.toHaveBeenCalled();
  });

  it("calls signUp and redirects to / on success", async () => {
    mockSignUp.mockResolvedValueOnce({ error: null });
    render(<SignInPage />);
    fireEvent.click(screen.getByRole("tab", { name: "Sign up" }));

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "new@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "password123" },
    });
    fireEvent.change(screen.getByLabelText("Confirm password"), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(mockSignUp).toHaveBeenCalledWith({
        email: "new@example.com",
        password: "password123",
      });
      expect(mockPush).toHaveBeenCalledWith("/");
    });
  });

  it("shows forgot password form when link is clicked", async () => {
    render(<SignInPage />);
    fireEvent.click(screen.getByText("Forgot password?"));

    expect(screen.getByText("← Back to sign in")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Send reset link" })).toBeInTheDocument();
  });

  it("calls resetPasswordForEmail and shows confirmation on success", async () => {
    mockResetPasswordForEmail.mockResolvedValueOnce({ error: null });
    render(<SignInPage />);
    fireEvent.click(screen.getByText("Forgot password?"));

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "user@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send reset link" }));

    await waitFor(() => {
      expect(mockResetPasswordForEmail).toHaveBeenCalledWith(
        "user@example.com",
        expect.objectContaining({ redirectTo: expect.stringContaining("/auth/callback") }),
      );
      expect(
        screen.getByText("Check your email for a reset link."),
      ).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Run tests — confirm they fail**

```bash
cd frontend && npx vitest run tests/auth/sign-in.test.tsx
```
Expected: FAIL — assertion errors because the old magic-link component renders, not the new tabs-based page.

---

## Task 4: Implement the sign-in page

**Files:**
- Modify: `frontend/app/(auth)/auth/sign-in/page.tsx` (rewrite the moved file)

- [ ] **Step 1: Replace the file content**

```tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

function ForgotPasswordForm({ onBack }: { onBack: () => void }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleReset(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const supabase = createBrowserSupabaseClient();
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/callback`,
    });
    setLoading(false);
    if (error) {
      setError(error.message);
    } else {
      setSent(true);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <button
        type="button"
        onClick={onBack}
        className="text-sm text-muted-foreground hover:text-foreground text-left w-fit"
      >
        ← Back to sign in
      </button>
      {sent ? (
        <p className="text-sm text-center text-muted-foreground">
          Check your email for a reset link.
        </p>
      ) : (
        <form onSubmit={handleReset} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Label htmlFor="reset-email">Email</Label>
            <Input
              id="reset-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          {error && <p className="text-sm text-destructive text-center">{error}</p>}
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Sending…" : "Send reset link"}
          </Button>
        </form>
      )}
    </div>
  );
}

function SignInForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showForgot, setShowForgot] = useState(false);

  if (showForgot) {
    return <ForgotPasswordForm onBack={() => setShowForgot(false)} />;
  }

  async function handleSignIn(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const supabase = createBrowserSupabaseClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      setError(error.message);
    } else {
      router.push("/");
    }
  }

  return (
    <form onSubmit={handleSignIn} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="signin-email">Email</Label>
        <Input
          id="signin-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="signin-password">Password</Label>
        <Input
          id="signin-password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
      </div>
      <button
        type="button"
        onClick={() => setShowForgot(true)}
        className="text-sm text-muted-foreground hover:text-foreground text-left w-fit"
      >
        Forgot password?
      </button>
      {error && <p className="text-sm text-destructive text-center">{error}</p>}
      <Button type="submit" disabled={loading} className="w-full">
        {loading ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}

function SignUpForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSignUp(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    setError(null);
    const supabase = createBrowserSupabaseClient();
    const { error } = await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (error) {
      setError(error.message);
    } else {
      router.push("/");
    }
  }

  return (
    <form onSubmit={handleSignUp} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="signup-email">Email</Label>
        <Input
          id="signup-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="signup-password">Password</Label>
        <Input
          id="signup-password"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
      </div>
      <div className="flex flex-col gap-2">
        <Label htmlFor="signup-confirm">Confirm password</Label>
        <Input
          id="signup-confirm"
          type="password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="••••••••"
        />
      </div>
      {error && <p className="text-sm text-destructive text-center">{error}</p>}
      <Button type="submit" disabled={loading} className="w-full">
        {loading ? "Creating account…" : "Create account"}
      </Button>
    </form>
  );
}

export default function SignInPage() {
  return (
    <Card className="w-full max-w-sm mx-4">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl">InboxIQ</CardTitle>
        <CardDescription>AI-powered email management</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="sign-in">
          <TabsList className="w-full">
            <TabsTrigger value="sign-in" className="flex-1">
              Sign in
            </TabsTrigger>
            <TabsTrigger value="sign-up" className="flex-1">
              Sign up
            </TabsTrigger>
          </TabsList>
          <TabsContent value="sign-in" className="mt-4">
            <SignInForm />
          </TabsContent>
          <TabsContent value="sign-up" className="mt-4">
            <SignUpForm />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: Run tests — confirm they all pass**

```bash
cd frontend && npx vitest run tests/auth/sign-in.test.tsx
```
Expected: 7 tests PASS.

- [ ] **Step 3: Run full test suite — confirm no regressions**

```bash
cd frontend && npx vitest run
```
Expected: all existing tests still pass.

- [ ] **Step 4: Commit**

```bash
git add app/\(auth\)/auth/sign-in/page.tsx tests/auth/sign-in.test.tsx
git commit -m "feat(auth): sign-in/sign-up screen with email+password and forgot password"
```

---

## Post-Implementation Checklist

- [ ] Supabase dashboard: disable email confirmation (Authentication → Settings → uncheck "Enable email confirmations") so sign-up redirects immediately to `/`
- [ ] Run `npx tsc --noEmit` in `frontend/` — no TypeScript errors
- [ ] Start dev server (`npm run dev`) and manually verify:
  - Navigating to `/auth/sign-in` shows the card with no AppNav
  - Navigating to `/` (unauthenticated) redirects to `/auth/sign-in`
  - Navigating to `/` (authenticated) shows the dashboard with AppNav
