"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { apiFetch } from "@/lib/api";
import type { ConnectedAccount, EmailDataDeleteCounts, User } from "@/types";

const CONTEXTS: User["default_context"][] = [
  "Job Hunting",
  "Shopping",
  "School Application",
  "Daily",
];

const NOTIFICATION_TAGS = [
  { key: "professor", label: "Professor" },
  { key: "friend", label: "Friend" },
  { key: "recruiter", label: "Recruiter" },
  { key: "custom", label: "Custom" },
] as const;

function toastForResult(connected: string, reason: string | null) {
  if (connected === "success") {
    toast.success("Gmail connected successfully");
  } else if (connected === "error") {
    if (reason === "user_cancelled") {
      toast.info("Connection cancelled");
    } else if (reason === "state_expired") {
      toast.error("Session expired — please try again");
    } else if (reason === "state_invalid") {
      toast.error("Invalid OAuth state — please try again");
    } else if (reason === "no_refresh_token") {
      toast.error("No refresh token — revoke Gmail access and reconnect");
    } else {
      toast.error(`Connection failed: ${reason ?? "unknown"}`);
    }
  }
}

function SettingsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [accounts, setAccounts] = useState<ConnectedAccount[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [notificationPrefs, setNotificationPrefs] = useState<Record<string, boolean>>({});
  const [retentionDays, setRetentionDays] = useState<string>("");
  const [savingSettings, setSavingSettings] = useState(false);
  const [pendingDisconnect, setPendingDisconnect] = useState<ConnectedAccount | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    const connected = searchParams.get("gmail_connected");
    const reason = searchParams.get("reason");
    if (connected) {
      toastForResult(connected, reason);
      router.replace("/settings");
    }
  }, [searchParams, router]);

  useEffect(() => {
    apiFetch<ConnectedAccount[]>("/accounts")
      .then(setAccounts)
      .catch(() => {});
    apiFetch<User>("/users/me")
      .then((loadedUser) => {
        setUser(loadedUser);
        setNotificationPrefs(loadedUser.notification_tag_preferences ?? {});
        setRetentionDays(
          loadedUser.data_retention_days ? String(loadedUser.data_retention_days) : "",
        );
      })
      .catch(() => {});
  }, []);

  async function connectGmail() {
    try {
      const { url } = await apiFetch<{ url: string }>("/auth/gmail/start");
      window.location.href = url;
    } catch {
      toast.error("Failed to start Gmail connection");
    }
  }

  async function confirmDisconnect() {
    if (!pendingDisconnect) return;
    const account = pendingDisconnect;
    setPendingDisconnect(null);
    try {
      await apiFetch(`/accounts/${account.id}`, { method: "DELETE" });
      setAccounts((prev) => prev.filter((a) => a.id !== account.id));
    } catch {
      toast.error(`Failed to disconnect ${account.email_address}`);
    }
  }

  async function updateDefaultContext(context: User["default_context"]) {
    const previous = user;
    if (previous) setUser({ ...previous, default_context: context });
    try {
      const response = await apiFetch<{ user: User }>("/users/me/context", {
        method: "PATCH",
        body: JSON.stringify({ context }),
      });
      setUser(response.user);
      toast.success("Default context updated");
    } catch {
      if (previous) setUser(previous);
      toast.error("Failed to update default context");
    }
  }

  async function saveSettings() {
    setSavingSettings(true);
    const days = retentionDays.trim() ? Number(retentionDays) : null;
    try {
      const updated = await apiFetch<User>("/users/me/settings", {
        method: "PATCH",
        body: JSON.stringify({
          notification_tag_preferences: notificationPrefs,
          data_retention_days: days,
        }),
      });
      setUser(updated);
      setNotificationPrefs(updated.notification_tag_preferences ?? {});
      setRetentionDays(updated.data_retention_days ? String(updated.data_retention_days) : "");
      toast.success("Settings saved");
    } catch {
      toast.error("Failed to save settings");
    } finally {
      setSavingSettings(false);
    }
  }

  async function deleteEmailData() {
    setDeleteOpen(false);
    try {
      const counts = await apiFetch<EmailDataDeleteCounts>("/users/me/email-data", {
        method: "DELETE",
      });
      toast.success(`Deleted ${counts.emails} emails and related AI records`);
    } catch {
      toast.error("Failed to delete stored email data");
    }
  }

  return (
    <main className="max-w-3xl space-y-8 p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <Button onClick={connectGmail}>Connect Gmail</Button>
      </div>

      <section>
        <h2 className="text-sm font-medium text-muted-foreground mb-3">
          Connected accounts
        </h2>

        {accounts.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No accounts connected. Click Connect Gmail to get started.
          </p>
        ) : (
          <ul className="space-y-2">
            {accounts.map((account) => (
              <li
                key={account.id}
                className="flex items-center justify-between rounded-lg border px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <span
                    className="h-3 w-3 rounded-full shrink-0"
                    style={{ backgroundColor: account.color ?? "#6b7280" }}
                  />
                  <div>
                    <p className="text-sm font-medium">{account.email_address}</p>
                    <p className="text-xs text-muted-foreground">
                      {account.last_synced
                        ? `Last synced ${formatDistanceToNow(new Date(account.last_synced))} ago`
                        : "Never synced"}
                    </p>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPendingDisconnect(account)}
                >
                  Disconnect
                </Button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-muted-foreground">Default context</h2>
        <div className="flex flex-wrap gap-2">
          {CONTEXTS.map((context) => (
            <Button
              key={context}
              type="button"
              size="sm"
              variant={user?.default_context === context ? "default" : "outline"}
              disabled={!user}
              onClick={() => updateDefaultContext(context)}
            >
              {context}
            </Button>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-muted-foreground">Notification preferences</h2>
        <div className="grid gap-3 rounded-lg border p-4 sm:grid-cols-2">
          {NOTIFICATION_TAGS.map((tag) => (
            <Label key={tag.key} className="flex items-center justify-between gap-3">
              <span>{tag.label}</span>
              <Switch
                checked={notificationPrefs[tag.key] ?? true}
                onCheckedChange={(checked) =>
                  setNotificationPrefs((current) => ({ ...current, [tag.key]: checked }))
                }
                aria-label={`Notify for ${tag.label}`}
              />
            </Label>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-muted-foreground">Privacy</h2>
        <div className="space-y-4 rounded-lg border p-4">
          <div className="space-y-1">
            <Label htmlFor="retention_days">Data retention days</Label>
            <Input
              id="retention_days"
              type="number"
              min={1}
              max={3650}
              placeholder="Keep indefinitely"
              value={retentionDays}
              onChange={(event) => setRetentionDays(event.target.value)}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={saveSettings} disabled={savingSettings}>
              {savingSettings ? "Saving..." : "Save settings"}
            </Button>
            <Button variant="destructive" onClick={() => setDeleteOpen(true)}>
              Delete stored email data
            </Button>
          </div>
        </div>
      </section>

      <AlertDialog
        open={pendingDisconnect !== null}
        onOpenChange={(open) => { if (!open) setPendingDisconnect(null); }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disconnect account?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to disconnect{" "}
              <span className="font-medium">{pendingDisconnect?.email_address}</span>?
              This will stop syncing emails from this account.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDisconnect}>
              Disconnect
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete stored email data?</AlertDialogTitle>
            <AlertDialogDescription>
              This removes stored emails, daily digests, and AI usage rows. Connected accounts and
              contact tags remain.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={deleteEmailData}>Delete data</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<main className="p-6 text-sm text-muted-foreground">Loading settings...</main>}>
      <SettingsPageContent />
    </Suspense>
  );
}
