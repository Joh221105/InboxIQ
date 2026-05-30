"use client";

import Link from "next/link";
import { Plus } from "lucide-react";

import { Bun } from "@/components/bun";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function EmptyDashboard() {
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-[18px] p-6">
      <Bun size={160} expr="empty" label="Bun holding an empty envelope, waiting for your inbox" />

      <h1 className="font-serif text-[28px] font-normal leading-tight text-foreground">
        Your inbox is waiting
      </h1>

      <p className="max-w-[360px] text-center text-[14.5px] leading-relaxed text-muted-foreground text-pretty">
        Connect a Gmail account and Bun will start sorting, summarizing, and
        surfacing what actually needs you.
      </p>

      <Link
        href="/settings"
        className={cn(
          buttonVariants(),
          "flex h-11 items-center gap-2 px-6 text-[15px]",
        )}
      >
        <Plus className="size-4" />
        Connect Gmail
      </Link>

      <p className="text-[12.5px] text-muted-foreground">
        Read-only access · disconnect anytime
      </p>
    </div>
  );
}
