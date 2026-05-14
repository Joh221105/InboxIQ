"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { EmailDetailPanel } from "@/components/inbox/email-detail-panel";
import { EmailList } from "@/components/inbox/email-list";
import { SearchBar } from "@/components/inbox/search-bar";
import { TriageTabs, emptyStateForTab } from "@/components/inbox/triage-tabs";
import { useEmailKeyboardNav } from "@/components/inbox/use-email-keyboard-nav";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api";
import { useArchiveEmail, useEmailCounts, useEmails } from "@/lib/queries/emails";
import type { ConnectedAccount, Email, TriageCategory } from "@/types";

function tabFromParam(value: string | null): "all" | TriageCategory {
  if (
    value === "action_required" ||
    value === "worth_reading" ||
    value === "auto_archive"
  ) {
    return value;
  }
  return "all";
}

function InboxPageContent() {
  const searchParams = useSearchParams();
  const tab = tabFromParam(searchParams.get("tab"));
  const q = searchParams.get("q") ?? "";
  const senderSearch = searchParams.get("sender_search") ?? "";
  const deepLinkedEmailId = searchParams.get("email_id");
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const emailsQuery = useEmails({ category: tab, search: q || undefined, senderSearch: senderSearch || undefined });
  const countsQuery = useEmailCounts();
  const archiveMutation = useArchiveEmail();

  const emails = useMemo(
    () => emailsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [emailsQuery.data],
  );
  const selectedEmail = emails.find((email) => email.id === selectedId) ?? null;
  const hasUnprocessed = emails.some((email) => email.ai_processed === false);

  useEffect(() => {
    if (!deepLinkedEmailId) return;
    if (!emails.some((email) => email.id === deepLinkedEmailId)) return;
    setSelectedId(deepLinkedEmailId);
    setPanelOpen(true);
  }, [deepLinkedEmailId, emails]);

  function selectEmail(email: Email) {
    setSelectedId(email.id);
    setPanelOpen(true);
  }

  function archiveEmail(email: Email) {
    archiveMutation.mutate(email.id);
    if (selectedId === email.id) {
      setSelectedId(null);
      setPanelOpen(false);
    }
  }

  async function syncNow() {
    setSyncing(true);
    try {
      const accounts = await apiFetch<ConnectedAccount[]>("/accounts");
      await Promise.all(
        accounts.map((account) => apiFetch(`/accounts/${account.id}/sync`, { method: "POST" })),
      );
      await emailsQuery.refetch();
      await countsQuery.refetch();
    } catch {
      toast.error("Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  useEmailKeyboardNav(
    emails,
    selectedId,
    setSelectedId,
    () => setPanelOpen(Boolean(selectedId)),
    () => {
      const email = emails.find((item) => item.id === selectedId);
      if (email) archiveEmail(email);
    },
    () => setPanelOpen(false),
    searchInputRef,
  );

  return (
    <div className="flex h-full flex-col">
      <header className="space-y-4 border-b px-6 py-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold">Inbox</h1>
            <p className="text-sm text-muted-foreground">Unified emails from connected accounts</p>
          </div>
          <Button onClick={syncNow} disabled={syncing}>
            {syncing ? "Syncing..." : "Sync now"}
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <SearchBar inputRef={searchInputRef} />
        </div>
        <TriageTabs value={tab} counts={countsQuery.data} />
      </header>

      {hasUnprocessed ? (
        <div className="border-b bg-amber-50 px-6 py-2 text-sm text-amber-900">
          Some emails are still being analyzed
        </div>
      ) : null}

      <section className="flex-1 px-6 py-4">
        {emailsQuery.isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-[88px] w-full" />
            <Skeleton className="h-[88px] w-full" />
            <Skeleton className="h-[88px] w-full" />
          </div>
        ) : (
          <EmailList
            emails={emails}
            selectedId={selectedId}
            onSelect={selectEmail}
            onArchive={archiveEmail}
            hasNextPage={Boolean(emailsQuery.hasNextPage)}
            fetchNextPage={() => void emailsQuery.fetchNextPage()}
            emptyText={emptyStateForTab(tab)}
          />
        )}
      </section>

      <EmailDetailPanel
        email={selectedEmail}
        open={panelOpen}
        onOpenChange={setPanelOpen}
        onArchive={archiveEmail}
      />
    </div>
  );
}

export default function InboxPage() {
  return (
    <Suspense fallback={<div className="p-6 text-sm text-muted-foreground">Loading inbox...</div>}>
      <InboxPageContent />
    </Suspense>
  );
}
