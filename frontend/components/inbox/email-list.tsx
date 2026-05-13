"use client";

import { useVirtualizer } from "@tanstack/react-virtual";
import { useEffect, useRef } from "react";

import { EmailCard } from "@/components/inbox/email-card";
import type { Email } from "@/types";

export function EmailList({
  emails,
  selectedId,
  onSelect,
  onArchive,
  hasNextPage,
  fetchNextPage,
  emptyText,
}: {
  emails: Email[];
  selectedId: string | null;
  onSelect: (email: Email) => void;
  onArchive: (email: Email) => void;
  hasNextPage: boolean;
  fetchNextPage: () => void;
  emptyText: string;
}) {
  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: emails.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 88,
    overscan: 8,
  });
  const virtualItems = rowVirtualizer.getVirtualItems();
  const lastVirtualItem = virtualItems[virtualItems.length - 1];

  useEffect(() => {
    if (hasNextPage && lastVirtualItem && lastVirtualItem.index >= emails.length - 5) {
      fetchNextPage();
    }
  }, [emails.length, fetchNextPage, hasNextPage, lastVirtualItem]);

  if (emails.length === 0) {
    return <div className="py-16 text-center text-sm text-muted-foreground">{emptyText}</div>;
  }

  return (
    <div ref={parentRef} className="h-[calc(100vh-190px)] overflow-auto">
      <div className="relative w-full" style={{ height: rowVirtualizer.getTotalSize() }}>
        {virtualItems.map((virtualItem) => {
          const email = emails[virtualItem.index];
          return (
            <div
              key={email.id}
              className="absolute left-0 top-0 w-full"
              style={{ transform: `translateY(${virtualItem.start}px)` }}
            >
              <EmailCard
                email={email}
                selected={selectedId === email.id}
                onClick={() => onSelect(email)}
                onArchive={() => onArchive(email)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}
