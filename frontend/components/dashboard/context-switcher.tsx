"use client";

import { cn } from "@/lib/utils";
import type { User } from "@/types";

const CONTEXTS: User["default_context"][] = [
  "Job Hunting",
  "Shopping",
  "School Application",
  "Daily",
];

export function ContextSwitcher({
  value,
  loading = false,
  onChange,
}: {
  value: User["default_context"];
  loading?: boolean;
  onChange: (context: User["default_context"]) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2" aria-label="Context mode">
      {CONTEXTS.map((context) => {
        const active = context === value;
        return (
          <button
            key={context}
            type="button"
            disabled={loading}
            onClick={() => onChange(context)}
            className={cn(
              "h-9 rounded-full border px-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60",
              active
                ? "border-primary bg-primary text-primary-foreground"
                : "border-input bg-background text-foreground hover:bg-accent",
            )}
          >
            {context}
          </button>
        );
      })}
    </div>
  );
}
