"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { cn } from "@/lib/utils";
import type { EmailCounts, TriageCategory } from "@/types";

const TABS: { value: "all" | TriageCategory; label: string; empty: string }[] = [
  { value: "all", label: "All", empty: "No emails yet" },
  { value: "action_required", label: "Action Required", empty: "No urgent emails right now. Nice." },
  { value: "worth_reading", label: "Worth Reading", empty: "Reading list is clear." },
  { value: "auto_archive", label: "Auto-Archived", empty: "Auto-archived emails will collect here." },
];

export function emptyStateForTab(tab: string) {
  return TABS.find((item) => item.value === tab)?.empty ?? TABS[0].empty;
}

export function TriageTabs({
  value,
  counts,
}: {
  value: "all" | TriageCategory;
  counts: EmailCounts | undefined;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function select(tab: "all" | TriageCategory) {
    const next = new URLSearchParams(searchParams.toString());
    if (tab === "all") next.delete("tab");
    else next.set("tab", tab);
    router.replace(`${pathname}?${next.toString()}`);
  }

  return (
    <div role="tablist" className="flex flex-wrap gap-1 border-b">
      {TABS.map((tab) => (
        <button
          key={tab.value}
          role="tab"
          type="button"
          aria-selected={value === tab.value}
          className={cn(
            "flex h-9 items-center gap-2 border-b-2 border-transparent px-3 text-sm text-muted-foreground",
            value === tab.value && "border-primary text-foreground",
          )}
          onClick={() => select(tab.value)}
        >
          <span>{tab.label}</span>
          <span className="rounded bg-muted px-1.5 py-0.5 text-xs">
            {counts?.[tab.value as keyof EmailCounts] ?? 0}
          </span>
        </button>
      ))}
    </div>
  );
}
