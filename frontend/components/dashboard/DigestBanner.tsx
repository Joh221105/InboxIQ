"use client";

import { format, formatDistanceToNow } from "date-fns";
import { Check } from "lucide-react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { Digest, DigestItem } from "@/types";

function splitSummary(summary: string): { lead: string; rest: string } {
  const words = summary.split(/\s+/).filter(Boolean);
  return {
    lead: words.slice(0, 5).join(" "),
    rest: words.slice(5).join(" "),
  };
}

function deadlineLabel(deadline: string | null): string | null {
  if (!deadline) return null;
  return `Due ${format(new Date(`${deadline}T00:00:00`), "MMM d")}`;
}

function DigestRow({ item }: { item: DigestItem }) {
  const router = useRouter();
  const parts = splitSummary(item.summary);
  const deadline = deadlineLabel(item.deadline);

  return (
    <li>
      <button
        type="button"
        onClick={() => router.push(`/inbox?email_id=${item.source_email_id}`)}
        className="w-full rounded-md px-2 py-1.5 text-left transition-colors hover:bg-background/70"
      >
        <span className="text-sm leading-6">
          <strong>{parts.lead}</strong>
          {parts.rest ? ` ${parts.rest}` : ""}
          <span className="text-muted-foreground"> - {item.sender}</span>
        </span>
        {deadline ? (
          <Badge className="ml-2 bg-background align-middle text-xs">
            {deadline}
          </Badge>
        ) : null}
      </button>
    </li>
  );
}

export function DigestBanner({ digest }: { digest: Digest | null | undefined }) {
  const generatedAt = digest?.generated_at ? new Date(digest.generated_at) : new Date();
  const updated = formatDistanceToNow(generatedAt, { addSuffix: false });
  const items = digest?.items ?? [];
  const degraded = digest?.degraded ?? false;

  return (
    <Card className="min-h-[188px] border-primary/20 bg-gradient-to-br from-primary/5 via-background to-background p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold">Today&apos;s briefing</h2>
          <p className="text-xs text-muted-foreground">Updated {updated} ago</p>
        </div>
        {digest?.context ? (
          <Badge className="bg-background text-xs">
            {digest.context}
          </Badge>
        ) : null}
      </div>

      {items.length > 0 ? (
        <ul className="list-disc space-y-1 pl-4">
          {items.map((item) => (
            <DigestRow key={item.source_email_id} item={item} />
          ))}
        </ul>
      ) : (
        <div className="flex min-h-[78px] items-center gap-2 text-sm text-muted-foreground">
          {!degraded ? <Check className="size-4 text-emerald-600" aria-hidden="true" /> : null}
          <span>{degraded ? "No recent action items available." : "Inbox calm. Nothing urgent today."}</span>
        </div>
      )}

      {degraded ? (
        <p className="mt-4 border-t pt-3 text-xs text-muted-foreground">
          Live digest unavailable - showing recent action items
        </p>
      ) : null}
    </Card>
  );
}
