"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { RefObject } from "react";
import { useEffect, useState, useTransition } from "react";

import { Input } from "@/components/ui/input";

export function SearchBar({
  inputRef,
}: {
  inputRef: RefObject<HTMLInputElement>;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [value, setValue] = useState(searchParams.get("q") ?? "");

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const next = new URLSearchParams(searchParams.toString());
      if (value) next.set("q", value);
      else next.delete("q");
      startTransition(() => router.replace(`${pathname}?${next.toString()}`));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [pathname, router, searchParams, value]);

  return (
    <Input
      ref={inputRef}
      value={value}
      onChange={(event) => setValue(event.target.value)}
      placeholder="Search keyword or sender"
      aria-label="Search emails"
      className="max-w-md"
      disabled={isPending}
    />
  );
}
