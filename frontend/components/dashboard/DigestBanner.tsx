"use client";

import { useState } from "react";
import { format, formatDistanceToNow } from "date-fns";
import { ChevronDown, ArrowRight, X } from "lucide-react";
import { useRouter } from "next/navigation";

import { Bun } from "@/components/bun";
import { Badge } from "@/components/ui/badge";
import type { Digest, DigestItem } from "@/types";

const STORAGE_KEY = "iq-digest-dismissed";

function deadlineLabel(deadline: string | null): string | null {
  if (!deadline) return null;
  return `Due ${format(new Date(`${deadline}T00:00:00`), "MMM d")}`;
}

function dotColor(item: DigestItem) {
  // Use a subtle colored dot based on whether the item has a deadline
  if (item.deadline) return "var(--triage-action)";
  return "var(--triage-read)";
}

function DigestRow({ item }: { item: DigestItem }) {
  const router = useRouter();
  const deadline = deadlineLabel(item.deadline);
  const color = dotColor(item);

  return (
    <li>
      <button
        type="button"
        onClick={() => router.push(`/inbox?email_id=${item.source_email_id}`)}
        className="flex w-full items-start gap-3 rounded-md px-2 py-1.5 text-left transition-colors duration-150 hover:bg-background/60"
      >
        <span
          className="mt-[7px] size-[6px] shrink-0 rounded-full"
          style={{ background: color }}
        />
        <span className="flex-1 text-[13.5px] leading-[1.4] text-secondary-foreground text-pretty">
          {item.summary}
          <span className="ml-1 text-muted-foreground">— {item.sender}</span>
        </span>
        {deadline ? (
          <Badge
            className="ml-1 shrink-0 self-start bg-background align-middle text-xs"
            style={{
              background: "var(--deadline-bg)",
              color: "var(--deadline-fg)",
              border: "none",
            }}
          >
            {deadline}
          </Badge>
        ) : null}
      </button>
    </li>
  );
}

export function DigestBanner({
  digest,
}: {
  digest: Digest | null | undefined;
}) {
  const [dismissed, setDismissed] = useState(
    () => typeof window !== "undefined" && localStorage.getItem(STORAGE_KEY) === "1",
  );
  const [expanded, setExpanded] = useState(false);

  const generatedAt = digest?.generated_at ? new Date(digest.generated_at) : new Date();
  const updated = formatDistanceToNow(generatedAt, { addSuffix: false });
  const items = digest?.items ?? [];
  const degraded = digest?.degraded ?? false;

  const INITIAL_ITEMS = 3;
  const shown = expanded ? items : items.slice(0, INITIAL_ITEMS);
  const hiddenCount = items.length - INITIAL_ITEMS;

  function dismiss() {
    setDismissed(true);
    localStorage.setItem(STORAGE_KEY, "1");
  }
  function restore() {
    setDismissed(false);
    localStorage.setItem(STORAGE_KEY, "0");
  }

  /* Dismissed — slim restore strip */
  if (dismissed) {
    return (
      <div
        className="flex items-center gap-3 rounded-[var(--radius)] border px-4 py-2.5"
        style={{
          background: "var(--secondary)",
          borderColor: "var(--border)",
        }}
      >
        <Bun size={22} expr="default" label="Bun mascot" />
        <span className="text-[13.5px] text-secondary-foreground">
          Briefing tucked away
          {items.length > 0 && (
            <span className="ml-1 text-muted-foreground">· {items.length} items</span>
          )}
        </span>
        <div className="flex-1" />
        <button
          type="button"
          onClick={restore}
          className="text-[13px] font-medium transition-colors duration-150"
          style={{ color: "var(--primary)" }}
        >
          Show briefing
        </button>
      </div>
    );
  }

  return (
    <div
      className="relative rounded-[var(--radius)] border p-4"
      style={{
        background: "var(--secondary)",
        borderColor: "var(--border)",
        boxShadow: "0 1px 2px oklch(0.40 0.03 60 / 0.06)",
      }}
    >
      {/* header row */}
      <div className="flex items-start gap-3">
        <Bun size={30} expr="default" label="Bun mascot" style={{ marginTop: 2, flexShrink: 0 }} />

        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-2.5">
            <h2 className="font-serif text-[18px] font-semibold leading-none text-secondary-foreground">
              Here&apos;s your briefing
            </h2>
            <span className="text-xs text-muted-foreground">
              Updated {updated} ago
              {digest?.context ? ` · ${digest.context}` : ""}
            </span>
          </div>

          {degraded ? (
            <p className="mt-2 text-[13px] italic text-muted-foreground">
              Summary unavailable — Bun couldn&apos;t reach the AI service just now.
            </p>
          ) : items.length === 0 ? (
            <p className="mt-2 text-[13px] text-muted-foreground">
              Inbox calm — nothing urgent today.
            </p>
          ) : (
            <ul className="mt-2.5 flex flex-col gap-0.5">
              {shown.map((item) => (
                <DigestRow key={item.source_email_id} item={item} />
              ))}
            </ul>
          )}

          {!degraded && hiddenCount > 0 && (
            <div className="mt-2 flex items-center gap-4">
              <button
                type="button"
                onClick={() => setExpanded((x) => !x)}
                className="flex h-6 items-center gap-1 text-[13px] transition-colors duration-150"
                style={{ color: "var(--muted-foreground)" }}
              >
                {expanded ? "Show less" : `Show ${hiddenCount} more`}
                <ChevronDown
                  className="size-[13px] transition-transform duration-150"
                  style={{ transform: expanded ? "rotate(180deg)" : "none" }}
                />
              </button>
              <button
                type="button"
                onClick={() => {}}
                className="flex h-6 items-center gap-1 text-[13px] font-medium transition-colors duration-150"
                style={{ color: "var(--primary)" }}
              >
                Open full briefing
                <ArrowRight className="size-[13px]" />
              </button>
            </div>
          )}
        </div>

        {/* dismiss */}
        <button
          type="button"
          aria-label="Dismiss briefing"
          onClick={dismiss}
          className="shrink-0 rounded-md p-1 transition-colors duration-150 hover:bg-background/60"
          style={{ color: "var(--muted-foreground)" }}
        >
          <X className="size-[15px]" />
        </button>
      </div>
    </div>
  );
}
