"use client";

import { Archive } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

import { AccountColorDot } from "@/components/inbox/account-color-dot";
import { ContactTagBadge } from "@/components/inbox/contact-tag-badge";
import { DeadlineBadge } from "@/components/inbox/deadline-badge";
import { TriageBadge } from "@/components/inbox/triage-badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Email, TriageCategory } from "@/types";

function categoryFor(email: Email): TriageCategory | null {
  const category = email.triage_category ?? email.ai_category;
  if (
    category === "action_required" ||
    category === "worth_reading" ||
    category === "auto_archive"
  ) {
    return category;
  }
  return null;
}

export function EmailCard({
  email,
  selected,
  onClick,
  onArchive,
}: {
  email: Email;
  selected: boolean;
  onClick: () => void;
  onArchive: () => void;
}) {
  const category = categoryFor(email);
  const summary =
    email.ai_summary || email.ai_processed === false ? email.ai_summary : null;
  const border =
    category === "action_required"
      ? "border-l-red-500"
      : category === "worth_reading"
        ? "border-l-amber-400"
        : "border-l-transparent";

  return (
    <div
      role="button"
      tabIndex={0}
      data-testid="email-card"
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
      className={cn(
        "grid h-[88px] w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 border border-l-[3px] bg-background px-4 text-left text-sm transition hover:bg-muted/50",
        border,
        category === "auto_archive" && "opacity-60",
        selected && "ring-2 ring-primary",
      )}
    >
      <AccountColorDot color={email.account_color} />
      <div className="min-w-0 space-y-1">
        <div className="flex min-w-0 items-center gap-2">
          <span className="truncate font-semibold">{email.sender ?? "(unknown)"}</span>
          <ContactTagBadge tag={email.contact_tag} />
        </div>
        <div className="truncate font-medium">{email.subject ?? "(no subject)"}</div>
        {summary ? (
          <div className="truncate text-muted-foreground">{summary}</div>
        ) : (
          <div className="truncate italic text-muted-foreground">AI processing...</div>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <DeadlineBadge date={email.deadline_extracted} />
        <TriageBadge category={category} />
        <span className="w-20 text-right text-xs text-muted-foreground">
          {email.received_at
            ? formatDistanceToNow(new Date(email.received_at), { addSuffix: true })
            : ""}
        </span>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label="Archive email"
          onClick={(event) => {
            event.stopPropagation();
            onArchive();
          }}
        >
          <Archive className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
