"use client";

import { Archive } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

import { AccountColorDot } from "@/components/inbox/account-color-dot";
import { ContactTagBadge } from "@/components/inbox/contact-tag-badge";
import { DeadlineBadge } from "@/components/inbox/deadline-badge";
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

function edgeBorderColor(
  category: TriageCategory | null,
  tagColor: string | undefined,
): string {
  if (category === "auto_archive") return "transparent";
  if (tagColor) return tagColor;
  if (category === "action_required") return "var(--triage-action)";
  if (category === "worth_reading")   return "var(--triage-read)";
  return "transparent";
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
  const tagColor  = email.contact_tag?.color ?? undefined;
  const borderColor = edgeBorderColor(category, tagColor);
  const isProcessing = !email.ai_processed && !email.ai_summary;

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
      style={{ borderLeftColor: borderColor }}
      className={cn(
        "grid h-[88px] w-full cursor-pointer grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 border-b border-l-[3px] bg-transparent px-4 text-left text-sm transition-colors duration-150 hover:bg-accent",
        category === "auto_archive" && "opacity-50",
        selected && "bg-accent ring-2 ring-inset ring-primary",
      )}
    >
      {/* col 1 — account dot + domain */}
      <AccountColorDot color={email.account_color} email={email.account_email} showLabel />

      {/* col 2 — content */}
      <div className="min-w-0 flex flex-col gap-[3px]">
        <div className="flex min-w-0 items-center gap-2">
          {!email.is_read && (
            <span
              className="size-[7px] shrink-0 rounded-full"
              style={{ background: "var(--primary)" }}
            />
          )}
          <span className="truncate text-[14px] font-semibold">
            {email.sender_name ?? email.sender ?? "(unknown)"}
          </span>
          <ContactTagBadge tag={email.contact_tag} sender={email.sender} />
        </div>
        <div className="truncate text-[14px] font-medium">
          {email.subject ?? "(no subject)"}
        </div>
        {isProcessing ? (
          /* AI shimmer state */
          <div className="flex items-center gap-2 h-[16px]">
            <span
              className="flex shrink-0 items-center gap-[5px] text-[11.5px] font-semibold"
              style={{ color: "var(--primary)" }}
            >
              <span className="ai-dot size-[6px] rounded-full" style={{ background: "var(--primary)" }} />
              Summarizing
            </span>
            <span className="skeleton-shimmer h-2 flex-1 max-w-[200px] rounded" />
          </div>
        ) : (
          <div className="truncate text-[13px] text-muted-foreground">
            {email.ai_summary ?? (
              <em className="not-italic">AI processing...</em>
            )}
          </div>
        )}
      </div>

      {/* col 3 — meta */}
      <div className="flex shrink-0 flex-col items-end gap-[7px]">
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {email.received_at
            ? formatDistanceToNow(new Date(email.received_at), { addSuffix: true })
            : ""}
        </span>
        <DeadlineBadge date={email.deadline_extracted} />
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
