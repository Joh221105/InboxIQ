import { Home } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function NotFound() {
  return (
    <main className="flex min-h-full items-center justify-center p-6">
      <section className="max-w-md text-center">
        <p className="text-sm font-medium text-muted-foreground">404</p>
        <h1 className="mt-2 text-2xl font-semibold">Page not found</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          This page is not part of your InboxIQ workspace.
        </p>
        <Link href="/" className={cn(buttonVariants(), "mt-6 gap-2")}>
          <Home className="size-4" aria-hidden="true" />
          Back to dashboard
        </Link>
      </section>
    </main>
  );
}
