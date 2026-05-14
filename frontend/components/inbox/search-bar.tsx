"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { RefObject } from "react";
import { useEffect, useState, useTransition } from "react";

import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

export function SearchBar({
  inputRef,
}: {
  inputRef: RefObject<HTMLInputElement>;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [bySender, setBySender] = useState(() => searchParams.has("sender_search"));
  const [value, setValue] = useState(
    searchParams.get("q") ?? searchParams.get("sender_search") ?? ""
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const next = new URLSearchParams(searchParams.toString());
      if (bySender) {
        if (value) next.set("sender_search", value);
        else next.delete("sender_search");
        next.delete("q");
      } else {
        if (value) next.set("q", value);
        else next.delete("q");
        next.delete("sender_search");
      }
      startTransition(() => router.replace(`${pathname}?${next.toString()}`));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [pathname, router, searchParams, value, bySender]);

  function handleToggleBySender() {
    setBySender((prev) => !prev);
  }

  return (
    <div className="flex items-center gap-2">
      <Input
        ref={inputRef}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder={bySender ? "Filter by sender name or email" : "Search keyword or sender"}
        aria-label="Search emails"
        className="max-w-md"
        disabled={isPending}
      />
      <button
        type="button"
        onClick={handleToggleBySender}
        disabled={isPending}
        aria-pressed={bySender}
        className={cn(
          "rounded-full px-2 py-0.5 text-xs border whitespace-nowrap",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          bySender ? "bg-primary text-primary-foreground border-primary" : "border-input text-muted-foreground"
        )}
      >
        By sender
      </button>
    </div>
  );
}
