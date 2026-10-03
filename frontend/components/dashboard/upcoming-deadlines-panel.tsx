"use client";

import { format } from "date-fns";

import { Card } from "@/components/ui/card";
import type { Email } from "@/types";

function dateLabel(value: string | null | undefined): string {
  if (!value) return "--";
  return format(new Date(`${value}T00:00:00`), "MMM d");
}

export function UpcomingDeadlinesPanel({ emails }: { emails: Email[] }) {
  return (
    <Card className="min-h-[260px] p-5">
      <h2 className="mb-4 text-base font-semibold">Upcoming Deadlines</h2>
      {emails.length === 0 ? (
        <div className="flex min-h-[178px] items-center text-sm text-muted-foreground">
          No deadlines in the next 7 days.
        </div>
      ) : (
        <ul className="space-y-3">
          {emails.map((email) => (
            <li key={email.id} className="grid grid-cols-[3.6rem_1fr] gap-3">
              <time className="font-mono text-sm text-muted-foreground">
                {dateLabel(email.deadline_extracted)}
              </time>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{email.subject ?? "(No subject)"}</p>
                <p className="truncate text-xs text-muted-foreground">{email.sender ?? "Unknown sender"}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
