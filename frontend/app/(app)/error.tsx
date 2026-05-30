"use client";

import { RotateCcw } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="flex min-h-full items-center justify-center p-6">
      <section className="max-w-md text-center">
        <p className="text-sm font-medium text-muted-foreground">Something went wrong</p>
        <h1 className="mt-2 text-2xl font-semibold">InboxIQ could not load this page</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Retry the request. If it keeps failing, check the backend health endpoint and browser console.
        </p>
        <Button onClick={reset} className="mt-6 gap-2">
          <RotateCcw className="size-4" aria-hidden="true" />
          Retry
        </Button>
      </section>
    </main>
  );
}
