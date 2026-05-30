"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { cn } from "@/lib/utils";
import type { EmailCounts, TriageCategory } from "@/types";

const TABS: { value: "all" | TriageCategory; label: string; empty: string }[] = [
  { value: "all",            label: "All",           empty: "No emails yet" },
  { value: "action_required",label: "Action Required", empty: "No urgent emails right now. Nice." },
  { value: "worth_reading",  label: "Worth Reading",  empty: "Reading list is clear." },
  { value: "auto_archive",   label: "Auto-Archived",  empty: "Auto-archived emails will collect here." },
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
    <div role="tablist" className="flex flex-wrap gap-[9px]">
      {TABS.map((tab) => {
        const active = value === tab.value;
        const count  = counts?.[tab.value as keyof EmailCounts] ?? 0;

        return (
          <button
            key={tab.value}
            role="tab"
            type="button"
            aria-selected={active}
            onClick={() => select(tab.value)}
            className={cn(
              "inline-flex h-[34px] items-center gap-[7px] rounded-full border px-[14px] text-[14px] font-medium leading-none transition-colors duration-150 whitespace-nowrap",
              active
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-transparent text-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            {tab.label}
            <span
              className={cn(
                "inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[12px] font-semibold",
                active
                  ? "bg-primary-foreground/25 text-primary-foreground"
                  : "bg-secondary text-secondary-foreground",
              )}
            >
              {count}
            </span>
          </button>
        );
      })}
    </div>
  );
}
