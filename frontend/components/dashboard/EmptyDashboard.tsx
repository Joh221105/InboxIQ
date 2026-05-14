"use client";

import { Inbox } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function EmptyDashboard() {
  return (
    <div className="flex min-h-full items-center justify-center p-6">
      <Card className="w-full max-w-md p-8 text-center">
        <div className="mx-auto mb-5 flex size-20 items-center justify-center rounded-full bg-primary/10">
          <Inbox className="size-10 text-primary" aria-hidden="true" />
        </div>
        <h1 className="text-2xl font-semibold">Connect your first inbox</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Bring Gmail into InboxIQ to start seeing briefings, deadlines, and pickup codes.
        </p>
        <Link href="/settings" className={cn(buttonVariants(), "mt-6")}>
          Connect inbox
        </Link>
      </Card>
    </div>
  );
}
