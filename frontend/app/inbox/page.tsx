"use client";

import { useEffect, useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import type { ConnectedAccount, EmailListPage } from "@/types";

export default function InboxPage() {
  const [emails, setEmails] = useState<EmailListPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  async function fetchEmails() {
    setLoading(true);
    try {
      const page = await apiFetch<EmailListPage>("/emails");
      setEmails(page);
    } catch {
      toast.error("Failed to load emails");
    } finally {
      setLoading(false);
    }
  }

  async function syncNow() {
    setSyncing(true);
    try {
      const accounts = await apiFetch<ConnectedAccount[]>("/accounts");
      await Promise.all(
        accounts.map((a) => apiFetch(`/accounts/${a.id}/sync`, { method: "POST" }))
      );
      await fetchEmails();
    } catch {
      toast.error("Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    void fetchEmails();
  }, []);

  return (
    <main className="p-6 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Inbox</h1>
        <Button onClick={syncNow} disabled={syncing}>
          {syncing ? "Syncing..." : "Sync now"}
        </Button>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : emails && emails.items.length > 0 ? (
        <ul className="space-y-1">
          {emails.items.map((email) => (
            <li
              key={email.id}
              className="flex items-center gap-3 rounded-lg border px-4 py-3 text-sm"
            >
              <span
                className="h-2.5 w-2.5 rounded-full shrink-0"
                style={{ backgroundColor: email.account_color ?? "#6b7280" }}
              />
              <span className="font-medium shrink-0 w-48 truncate">
                {email.sender ?? "(unknown)"}
              </span>
              <span className="flex-1 truncate text-muted-foreground">
                {email.subject ?? "(no subject)"}
              </span>
              <span className="text-xs text-muted-foreground shrink-0">
                {email.received_at
                  ? formatDistanceToNow(new Date(email.received_at), { addSuffix: true })
                  : ""}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">
          No emails yet — click Sync now.
        </p>
      )}
    </main>
  );
}
