"use client";

import Link from "next/link";
import { Plus } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function EmptyDashboard() {
  return (
    <div className="flex min-h-full h-full flex-col items-center justify-center gap-[18px] p-6" style={{ background: "#dedbd5" }}>
      <div className="relative h-[200px] w-[154px] overflow-hidden" style={{ background: "#dedbd5" }}>
        <video
          src="/bun-idle.mp4"
          autoPlay
          loop
          muted
          playsInline
          aria-label="Bun holding an empty envelope, waiting for your inbox"
          className="absolute left-1/2 top-0 h-full w-auto max-w-none -translate-x-1/2 mix-blend-multiply"
        />
      </div>

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
