import { differenceInCalendarDays, format, startOfToday } from "date-fns";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function DeadlineBadge({ date }: { date: string | null | undefined }) {
  if (!date) return null;

  const due = new Date(`${date}T00:00:00`);
  const days = differenceInCalendarDays(due, startOfToday());
  return (
    <Badge
      className={cn(
        "shrink-0",
        days < 0 && "border-red-200 bg-red-50 text-red-700",
        days >= 0 && days <= 3 && "border-amber-200 bg-amber-50 text-amber-800",
        days > 3 && "border-border bg-background text-muted-foreground",
      )}
    >
      Due {format(due, "MMM d")}
    </Badge>
  );
}
