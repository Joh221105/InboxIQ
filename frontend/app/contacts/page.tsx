"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

import { AddContactDialog } from "@/components/contacts/AddContactDialog";
import { TagSection } from "@/components/contacts/TagSection";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useContacts } from "@/lib/queries/contacts";

export default function ContactsPage() {
  const contacts = useContacts();
  const [dialogOpen, setDialogOpen] = useState(false);

  const data = contacts.data;
  const totalTags = data
    ? data.professor.length + data.friend.length + data.recruiter.length + data.custom.length
    : 0;

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
          <TagSection type="professor" tags={data!.professor} />
          <TagSection type="recruiter" tags={data!.recruiter} />
          <TagSection type="friend" tags={data!.friend} />
          <TagSection type="custom" tags={data!.custom} />
        </div>
      )}
    </main>
  );
}
