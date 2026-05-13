import { Badge } from "@/components/ui/badge";
import type { TriageCategory } from "@/types";

const LABELS: Record<TriageCategory, string> = {
  action_required: "Action required",
  worth_reading: "Worth reading",
  auto_archive: "Auto archive",
};

const CLASSES: Record<TriageCategory, string> = {
  action_required: "border-red-200 bg-red-50 text-red-700",
  worth_reading: "border-amber-200 bg-amber-50 text-amber-800",
  auto_archive: "border-muted bg-muted text-muted-foreground",
};

export function TriageBadge({ category }: { category: TriageCategory | null | undefined }) {
  if (!category) return null;
  return (
    <Badge
      className={CLASSES[category]}
      aria-label={`Triage category: ${LABELS[category]}`}
    >
      {LABELS[category]}
    </Badge>
  );
}
