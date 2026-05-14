"use client";

import { cn } from "@/lib/utils";

export function Switch({
  checked,
  onCheckedChange,
  "aria-label": ariaLabel,
}: {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  "aria-label"?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel}
      className={cn(
        "inline-flex h-6 w-11 items-center rounded-full border transition",
        checked ? "border-primary bg-primary" : "border-border bg-muted",
      )}
      onClick={() => onCheckedChange(!checked)}
    >
      <span
        className={cn(
          "size-5 rounded-full bg-background shadow-sm transition",
          checked ? "translate-x-5" : "translate-x-0.5",
        )}
      />
    </button>
  );
}
