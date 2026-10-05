"use client";

import { Plus } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import { AddContactDialog } from "@/components/contacts/add-contact-dialog";
import { TagSection } from "@/components/contacts/tag-section";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useContactEmailHistory, useContacts } from "@/lib/queries/contacts";
import type { ContactTag } from "@/types";

function allTags(data: ReturnType<typeof useContacts>["data"]): ContactTag[] {
  if (!data) return [];
  return [...data.professor, ...data.recruiter, ...data.friend, ...data.custom];
}

function ContactsPageContent() {
  const contacts = useContacts();
  const searchParams = useSearchParams();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedTag, setSelectedTag] = useState<ContactTag | null>(null);

  const data = contacts.data;
  const tags = useMemo(() => allTags(data), [data]);
  const totalTags = data
    ? data.professor.length + data.friend.length + data.recruiter.length + data.custom.length
    : 0;
  const history = useContactEmailHistory(selectedTag?.id ?? null);

  useEffect(() => {
    const identifier = searchParams.get("identifier");
    if (!identifier || tags.length === 0) return;
    const normalized = identifier.toLowerCase();
    const match = tags.find((tag) => tag.identifier.toLowerCase() === normalized);
    if (match) setSelectedTag(match);
  }, [searchParams, tags]);

  return (
    <main className="max-w-2xl space-y-6 p-6">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Contacts</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Tagged senders appear as colored badges across your inbox.
          </p>
        </div>
        <Button size="sm" onClick={() => setDialogOpen(true)}>
          <Plus className="mr-1.5 size-4" aria-hidden="true" />
          Add tag
        </Button>
      </header>

      <AddContactDialog open={dialogOpen} onOpenChange={setDialogOpen} />

      {contacts.isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-10 w-full rounded-md" />
          ))}
        </div>
      ) : contacts.isError ? (
        <p className="text-sm text-destructive">Failed to load contacts.</p>
      ) : totalTags === 0 ? (
        <section className="rounded-lg border border-dashed p-10 text-center">
          <p className="text-sm font-medium">No tagged contacts yet</p>
          <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
            Add a sender tag to highlight recruiters, professors, friends, and custom groups in
            your inbox.
          </p>
          <Button
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => setDialogOpen(true)}
          >
            <Plus className="mr-1.5 size-4" aria-hidden="true" />
            Add your first tag
          </Button>
        </section>
      ) : (
        <div className="space-y-6">
          <TagSection
            type="professor"
            tags={data!.professor}
            selectedId={selectedTag?.id ?? null}
            onSelect={setSelectedTag}
          />
          <TagSection
            type="recruiter"
            tags={data!.recruiter}
            selectedId={selectedTag?.id ?? null}
            onSelect={setSelectedTag}
          />
          <TagSection
            type="friend"
            tags={data!.friend}
            selectedId={selectedTag?.id ?? null}
            onSelect={setSelectedTag}
          />
          <TagSection
            type="custom"
            tags={data!.custom}
            selectedId={selectedTag?.id ?? null}
            onSelect={setSelectedTag}
          />
        </div>
      )}

      {selectedTag ? (
        <section className="space-y-3 rounded-lg border p-4">
          <div>
            <h2 className="text-sm font-semibold">Email history</h2>
            <p className="text-sm text-muted-foreground">{selectedTag.identifier}</p>
          </div>
          {history.isLoading ? (
            <Skeleton className="h-20 w-full rounded-md" />
          ) : history.data?.items.length ? (
            <ul className="divide-y rounded-md border">
              {history.data.items.slice(0, 10).map((email) => (
                <li key={email.id} className="px-3 py-2 text-sm">
                  <div className="truncate font-medium">{email.subject ?? "(no subject)"}</div>
                  <div className="truncate text-xs text-muted-foreground">
                    {email.sender ?? "(unknown sender)"}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
              No matching email history yet.
            </p>
          )}
        </section>
      ) : null}
    </main>
  );
}

export default function ContactsPage() {
  return (
    <Suspense fallback={<main className="p-6 text-sm text-muted-foreground">Loading contacts...</main>}>
      <ContactsPageContent />
    </Suspense>
  );
}
