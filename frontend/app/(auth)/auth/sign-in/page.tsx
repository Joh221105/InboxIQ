"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Bun } from "@/components/bun";

/* ── Forgot-password sub-form ───────────────────────────────── */
function ForgotPasswordForm({ onBack }: { onBack: () => void }) {
  const [email, setEmail]   = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent]     = useState(false);
  const [error, setError]   = useState<string | null>(null);

  async function handleReset(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const supabase = createBrowserSupabaseClient();
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/auth/callback?next=/auth/update-password`,
    });
    setLoading(false);
    if (error) setError(error.message);
    else setSent(true);
  }

  return (
    <div className="flex flex-col gap-4">
      <Button
        variant="ghost"
        type="button"
        onClick={onBack}
        className="h-auto px-0 text-sm text-muted-foreground hover:text-foreground"
      >
        ← Back to sign in
      </Button>
      {sent ? (
        <p className="text-center text-sm text-muted-foreground">
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
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          {error && (
            <p role="alert" className="text-center text-sm text-destructive">
              {error}
            </p>
          )}
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Sending…" : "Send reset link"}
          </Button>
        </form>
      )}
    </div>
  );
}

/* ── Sign-in form ────────────────────────────────────────────── */
function SignInForm() {
  const router = useRouter();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);
  const [showForgot, setShowForgot] = useState(false);

  if (showForgot) return <ForgotPasswordForm onBack={() => setShowForgot(false)} />;

  async function handleSignIn(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const supabase = createBrowserSupabaseClient();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) setError(error.message);
    else router.replace("/");
  }

  return (
    <form onSubmit={handleSignIn} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="signin-email">Email</Label>
        <Input
          id="signin-email"
          type="email"
          required
          autoComplete="email"
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
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
      </div>
      <Button
        variant="ghost"
        type="button"
        onClick={() => setShowForgot(true)}
        className="h-auto self-start px-0 text-sm text-muted-foreground hover:text-foreground"
      >
        Forgot password?
      </Button>
      {error && (
        <p role="alert" className="text-center text-sm text-destructive">
          {error}
        </p>
      )}
      <Button type="submit" disabled={loading} className="w-full">
        {loading ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}

/* ── Sign-up form ────────────────────────────────────────────── */
function SignUpForm() {
  const router = useRouter();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm]   = useState("");
  const [error, setError]       = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);

  async function handleSignUp(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    setError(null);
    const supabase = createBrowserSupabaseClient();
    const { data, error } = await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (error) setError(error.message);
    else if (!data.session) setError("Check your email to confirm your account before signing in.");
    else router.replace("/");
  }

  return (
    <form onSubmit={handleSignUp} className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="signup-email">Email</Label>
        <Input
          id="signup-email"
          type="email"
          required
          autoComplete="email"
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
          autoComplete="new-password"
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
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          placeholder="••••••••"
        />
      </div>
      {error && (
        <p role="alert" className="text-center text-sm text-destructive">
          {error}
        </p>
      )}
      <Button type="submit" disabled={loading} className="w-full">
        {loading ? "Creating account…" : "Create account"}
      </Button>
    </form>
  );
}

/* ── Page ────────────────────────────────────────────────────── */
export default function SignInPage() {
  const [tab, setTab] = useState<"sign-in" | "sign-up">("sign-in");

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* left brand panel */}
      <div
        className="hidden flex-col justify-between p-10 lg:flex lg:flex-1"
        style={{
          background:   "var(--sidebar)",
          borderRight:  "1px solid var(--sidebar-border)",
        }}
      >
        {/* top wordmark */}
        <div className="flex items-center gap-2.5">
          <Bun size={28} envelope={false} label="InboxIQ logo" />
          <span className="font-serif text-[22px] font-semibold leading-none">
            InboxIQ
          </span>
        </div>

        {/* center tagline */}
        <div className="max-w-[340px]">
          <h1 className="font-serif text-[40px] font-normal leading-[1.12] tracking-[-0.01em]">
            The inbox that handles itself.
          </h1>
          <p className="mt-[14px] text-[15px] leading-relaxed text-muted-foreground">
            Bun sorts your mail by urgency, pulls out deadlines and pickup codes,
            and tucks the noise away — so opening your inbox feels calm.
          </p>
        </div>

        {/* Bun illustration with ear-bob */}
        <Bun size={132} expr="loading" bob label="Bun the rabbit mascot" />
      </div>

      {/* right form panel */}
      <div className="relative flex w-full flex-col items-center justify-center px-6 lg:w-[420px] lg:px-12">
        <div className="w-full max-w-[320px]">
          {/* heading */}
          <div className="mb-6">
            <h2 className="text-[24px] font-semibold">
              {tab === "sign-in" ? "Welcome back" : "Create account"}
            </h2>
            <p className="mt-1 text-[14px] text-muted-foreground">
              {tab === "sign-in"
                ? "Sign in to your InboxIQ account"
                : "Join InboxIQ to start managing your inbox"}
            </p>
          </div>

          {/* tab switcher */}
          <div
            className="mb-5 flex rounded-full border p-[3px]"
            style={{ background: "var(--muted)", borderColor: "var(--border)" }}
          >
            {(["sign-in", "sign-up"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTab(t)}
                className="flex-1 rounded-full py-1.5 text-[13.5px] font-medium transition-colors duration-150"
                style={
                  tab === t
                    ? { background: "var(--card)", color: "var(--foreground)", boxShadow: "0 1px 3px oklch(0.40 0.03 60 / 0.08)" }
                    : { color: "var(--muted-foreground)" }
                }
              >
                {t === "sign-in" ? "Sign in" : "Sign up"}
              </button>
            ))}
          </div>

          {tab === "sign-in" ? <SignInForm /> : <SignUpForm />}
        </div>
      </div>
    </div>
  );
}
