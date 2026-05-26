"use client";

import { Trash2 } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useDeleteContact } from "@/lib/queries/contacts";
import type { ContactTag, TagType } from "@/types";

const SECTION_LABELS: Record<TagType, string> = {
  professor: "Professors",
  friend: "Friends",
  recruiter: "Recruiters",
  custom: "Custom",
};

function getTagLabel(tag: ContactTag): string {
  if (tag.custom_label) return tag.custom_label;
  return SECTION_LABELS[tag.tag] ?? tag.tag;
}

function ContactRow({
  tag,
  selected,
  onSelect,
}: {
  tag: ContactTag;
  selected: boolean;
  onSelect: (tag: ContactTag) => void;
}) {
  const deleteContact = useDeleteContact();

  return (
    <div className="flex items-center justify-between gap-3 rounded-md border px-3 py-2">
      <button
        type="button"
        className="flex min-w-0 flex-1 items-center gap-2 text-left"
        onClick={() => onSelect(tag)}
        aria-pressed={selected}
      >
        <span
          className="size-3 shrink-0 rounded-full"
          style={{ backgroundColor: tag.color }}
          aria-hidden="true"
        />
        <span className="truncate text-sm font-mono">{tag.identifier}</span>
        <span
          className="shrink-0 rounded px-1.5 py-0.5 text-xs font-medium text-white"
          style={{ backgroundColor: tag.color }}
        >
          {getTagLabel(tag)}
        </span>
      </button>
      <AlertDialog>
        <AlertDialogTrigger
          className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:text-destructive focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          aria-label={`Remove tag for ${tag.identifier}`}
        >
          <Trash2 className="size-3.5" aria-hidden="true" />
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove tag?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove the tag from <strong>{tag.identifier}</strong> and clear the badge
              from all matching emails.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteContact.mutate(tag.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export function TagSection({
  type,
  tags,
  selectedId,
  onSelect,
}: {
  type: TagType;
  tags: ContactTag[];
  selectedId: string | null;
  onSelect: (tag: ContactTag) => void;
}) {
  return (
    <section>
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {SECTION_LABELS[type]}
      </h2>
      {tags.length === 0 ? (
        <p className="text-sm italic text-muted-foreground">
          No {SECTION_LABELS[type].toLowerCase()} contacts yet.
        </p>
      ) : (
        <div className="space-y-2">
          {tags.map((tag) => (
            <ContactRow
              key={tag.id}
              tag={tag}
              selected={selectedId === tag.id}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </section>
  );
}
