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
import { useConnectedAccounts, useUserContext } from "@/lib/queries/dashboard";
import { useDeleteEmailData, useDisconnectAccount, useUpdateSettings } from "@/lib/queries/settings";
import type { ConnectedAccount, User } from "@/types";

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

async function connectGmail() {
  try {
    const { url } = await apiFetch<{ url: string }>("/auth/gmail/start");
    if (new URL(url).hostname !== "accounts.google.com") {
      toast.error("Invalid OAuth redirect — please try again");
      return;
    }
    window.location.href = url;
  } catch {
    toast.error("Failed to start Gmail connection");
  }
}

/** Form state is initialized once from the loaded user; the parent keys it by user id. */
function PreferencesForm({ user, onDeleteRequested }: { user: User; onDeleteRequested: () => void }) {
  const updateSettings = useUpdateSettings();
  const [notificationPrefs, setNotificationPrefs] = useState<Record<string, boolean>>(
    user.notification_tag_preferences ?? {},
  );
  const [retentionDays, setRetentionDays] = useState(
    user.data_retention_days ? String(user.data_retention_days) : "",
  );

  function save() {
    updateSettings.mutate({
      notification_tag_preferences: notificationPrefs,
      data_retention_days: retentionDays.trim() ? Number(retentionDays) : null,
    });
  }

  return (
    <>
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
            <Button onClick={save} disabled={updateSettings.isPending}>
              {updateSettings.isPending ? "Saving..." : "Save settings"}
            </Button>
            <Button variant="destructive" onClick={onDeleteRequested}>
              Delete stored email data
            </Button>
          </div>
        </div>
      </section>
    </>
  );
}

function AccountList({
  accounts,
  onDisconnect,
}: {
  accounts: ConnectedAccount[];
  onDisconnect: (account: ConnectedAccount) => void;
}) {
  if (accounts.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No accounts connected. Click Connect Gmail to get started.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {accounts.map((account) => {
        const isDisconnected = Boolean(account.disconnected_at);
        return (
          <li
            key={account.id}
            className="flex items-center justify-between rounded-lg border px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <span
                className="h-3 w-3 shrink-0 rounded-full"
                style={{ backgroundColor: isDisconnected ? "#ef4444" : (account.color ?? "#6b7280") }}
              />
              <div>
                <p className="text-sm font-medium">{account.email_address}</p>
                <p className="text-xs text-muted-foreground">
                  {isDisconnected
                    ? "Connection expired — reconnect to resume syncing"
                    : account.last_synced
                      ? `Last synced ${formatDistanceToNow(new Date(account.last_synced))} ago`
                      : "Never synced"}
                </p>
              </div>
            </div>

            {isDisconnected ? (
              <Button size="sm" onClick={connectGmail}>
                Reconnect
              </Button>
            ) : (
              <Button variant="outline" size="sm" onClick={() => onDisconnect(account)}>
                Disconnect
              </Button>
            )}
          </li>
        );
      })}
    </ul>
  );
}

function SettingsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const accountsQuery = useConnectedAccounts();
  const userQuery = useUserContext();
  const disconnect = useDisconnectAccount();
  const deleteEmailData = useDeleteEmailData();
  const [pendingDisconnect, setPendingDisconnect] = useState<ConnectedAccount | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);

  useEffect(() => {
    const connected = searchParams.get("gmail_connected");
    if (connected) {
      toastForResult(connected, searchParams.get("reason"));
      router.replace("/settings");
    }
  }, [searchParams, router]);

  function confirmDisconnect() {
    if (!pendingDisconnect) return;
    const account = pendingDisconnect;
    setPendingDisconnect(null);
    disconnect.mutate(account);
  }

  return (
    <main className="max-w-3xl space-y-8 p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <Button onClick={connectGmail}>Connect Gmail</Button>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">Connected accounts</h2>
        {accountsQuery.isError ? (
          <p className="text-sm text-destructive">Couldn&apos;t load connected accounts.</p>
        ) : (
          <AccountList accounts={accountsQuery.data ?? []} onDisconnect={setPendingDisconnect} />
        )}
      </section>

      {userQuery.data ? (
        <PreferencesForm
          key={userQuery.data.id}
          user={userQuery.data}
          onDeleteRequested={() => setDeleteOpen(true)}
        />
      ) : null}

      <AlertDialog
        open={pendingDisconnect !== null}
        onOpenChange={(open) => {
          if (!open) setPendingDisconnect(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disconnect account?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to disconnect{" "}
              <span className="font-medium">{pendingDisconnect?.email_address}</span>? This will
              stop syncing emails from this account.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDisconnect}>Disconnect</AlertDialogAction>
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
            <AlertDialogAction
              onClick={() => {
                setDeleteOpen(false);
                deleteEmailData.mutate();
              }}
            >
              Delete data
            </AlertDialogAction>
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
