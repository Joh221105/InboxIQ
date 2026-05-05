"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { createBrowserSupabaseClient } from "@/lib/supabase/client";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { Session } from "@supabase/supabase-js";

type MessageRow = {
  id: string;
  subject?: string | null;
  from?: string | null;
  date?: string | null;
  snippet?: string | null;
};

function getApiBase(): string {
  const u = process.env.NEXT_PUBLIC_API_URL;
  if (!u) throw new Error("NEXT_PUBLIC_API_URL is not set");
  return u.replace(/\/$/, "");
}

export function InboxHome() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [banner, setBanner] = useState<string | null>(null);
  const [emailsLoading, setEmailsLoading] = useState(false);
  const [emailsError, setEmailsError] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageRow[]>([]);

  const refreshSession = useCallback(async () => {
    const supabase = createBrowserSupabaseClient();
    const { data } = await supabase.auth.getSession();
    setSession(data.session ?? null);
    setLoading(false);
  }, []);

  useEffect(() => {
    void refreshSession();
    const supabase = createBrowserSupabaseClient();
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, sess) => {
      setSession(sess);
    });
    return () => subscription.unsubscribe();
  }, [refreshSession]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("gmail") === "connected") {
      setBanner("Gmail connected successfully.");
      window.history.replaceState({}, "", window.location.pathname);
    }
    const err = params.get("gmail_error");
    if (err) {
      setBanner(`Gmail connection failed: ${decodeURIComponent(err)}`);
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  async function connectGmail() {
    setBanner(null);
    if (!session) {
      setBanner("Sign in first.");
      return;
    }
    try {
      const res = await fetch(`${getApiBase()}/auth/gmail/start`, {
        method: "POST",
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setBanner(typeof body.detail === "string" ? body.detail : "Could not start Gmail OAuth.");
        return;
      }
      const data = (await res.json()) as { authorization_url?: string };
      if (!data.authorization_url) {
        setBanner("Invalid response from API.");
        return;
      }
      window.location.href = data.authorization_url;
    } catch {
      setBanner("Network error — is the API running?");
    }
  }

  async function loadEmails() {
    setEmailsError(null);
    setMessages([]);
    if (!session) {
      setEmailsError("Sign in first.");
      return;
    }
    setEmailsLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/emails?limit=25`, {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setEmailsError(typeof data.detail === "string" ? data.detail : "Failed to load emails.");
        return;
      }
      const list = (data as { messages?: MessageRow[] }).messages ?? [];
      setMessages(list);
      if (list.length >= 10) {
        setBanner(`Loaded ${list.length} messages from Gmail (meets the ≥10 check).`);
      } else if (list.length > 0) {
        setBanner(
          `Loaded ${list.length} message(s). Gmail returned fewer than 10 threads in this mailbox — use an account with more history for the full acceptance check.`
        );
      }
    } catch {
      setEmailsError("Network error — is the API running?");
    } finally {
      setEmailsLoading(false);
    }
  }

  async function signOut() {
    const supabase = createBrowserSupabaseClient();
    await supabase.auth.signOut();
    setMessages([]);
    setBanner(null);
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-muted-foreground">
        Loading…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-muted/20">
      <header className="border-b bg-background/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-4">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">InboxIQ</h1>
            <p className="text-xs text-muted-foreground">Connect Gmail and preview messages</p>
          </div>
          <div className="flex items-center gap-2">
            {session ? (
              <>
                <span className="hidden text-xs text-muted-foreground sm:inline max-w-[200px] truncate">
                  {session.user.email}
                </span>
                <Button type="button" variant="outline" size="sm" onClick={() => void signOut()}>
                  Sign out
                </Button>
              </>
            ) : (
              <Link href="/login" className={cn(buttonVariants({ size: "sm" }))}>
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        {banner ? (
          <p className="rounded-lg border bg-card px-4 py-3 text-sm text-card-foreground">{banner}</p>
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>Gmail</CardTitle>
            <CardDescription>
              OAuth runs on the API server; tokens are stored in Supabase (server-side only).
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3">
            <Button type="button" onClick={() => void connectGmail()} disabled={!session}>
              Connect Gmail
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => void loadEmails()}
              disabled={!session || emailsLoading}
            >
              {emailsLoading ? "Loading…" : "Fetch recent emails"}
            </Button>
          </CardContent>
        </Card>

        {emailsError ? (
          <p className="text-sm text-destructive" role="alert">
            {emailsError}
          </p>
        ) : null}

        {messages.length > 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>Inbox preview</CardTitle>
              <CardDescription>
                {messages.length} message{messages.length === 1 ? "" : "s"} (up to 25 from Gmail)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <ul className="space-y-3">
                {messages.map((m) => (
                  <li
                    key={m.id}
                    className="rounded-lg border bg-background/60 px-3 py-2 text-sm shadow-sm"
                  >
                    <div className="font-medium leading-snug">{m.subject || "(No subject)"}</div>
                    <div className="text-xs text-muted-foreground">{m.from}</div>
                    {m.snippet ? (
                      <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{m.snippet}</p>
                    ) : null}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ) : null}
      </main>
    </div>
  );
}
