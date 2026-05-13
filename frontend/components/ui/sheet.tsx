"use client";

import * as React from "react";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Sheet({
  open,
  onOpenChange,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}) {
  React.useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onOpenChange(false);
    }
    if (open) window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/20" onMouseDown={() => onOpenChange(false)}>
      {children}
    </div>
  );
}

export function SheetContent({
  className,
  children,
  onClose,
}: {
  className?: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <section
      role="dialog"
      aria-modal="true"
      className={cn(
        "fixed right-0 top-0 h-full w-full max-w-2xl overflow-auto border-l bg-background shadow-xl md:w-[560px]",
        "max-md:bottom-0 max-md:top-auto max-md:h-[82vh] max-md:max-w-none max-md:rounded-t-lg max-md:border-l-0 max-md:border-t",
        className,
      )}
      onMouseDown={(event) => event.stopPropagation()}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute right-3 top-3"
        onClick={onClose}
        aria-label="Close"
      >
        <X className="h-4 w-4" />
      </Button>
      {children}
    </section>
  );
}
