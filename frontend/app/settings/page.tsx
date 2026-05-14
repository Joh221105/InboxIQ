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
import { apiFetch } from "@/lib/api";
import type { ConnectedAccount } from "@/types";

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
  const [pendingDisconnect, setPendingDisconnect] = useState<ConnectedAccount | null>(null);

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
      .catch(() => toast.error("Failed to load connected accounts"));
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

  return (
    <main className="p-6 max-w-2xl">
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
