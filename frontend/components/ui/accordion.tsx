"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

export function Accordion({
  open,
  onOpenChange,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}) {
  return (
    <div data-state={open ? "open" : "closed"} className="border-t">
      {React.Children.map(children, (child) =>
        React.isValidElement(child)
          ? React.cloneElement(child as React.ReactElement<{ open?: boolean; onOpenChange?: (open: boolean) => void }>, {
              open,
              onOpenChange,
            })
          : child,
      )}
    </div>
  );
}

export function AccordionItem({
  open = false,
  onOpenChange,
  children,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
}) {
  return (
    <section>
      {React.Children.map(children, (child) =>
        React.isValidElement(child)
          ? React.cloneElement(child as React.ReactElement<{ open?: boolean; onOpenChange?: (open: boolean) => void }>, {
              open,
              onOpenChange,
            })
          : child,
      )}
    </section>
  );
}

export function AccordionTrigger({
  open = false,
  onOpenChange,
  children,
  className,
}: {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <button
      type="button"
      aria-expanded={open}
      className={cn("flex w-full items-center justify-between py-4 text-left text-sm font-medium", className)}
      onClick={() => onOpenChange?.(!open)}
    >
      {children}
      <span aria-hidden="true">{open ? "-" : "+"}</span>
    </button>
  );
}

export function AccordionContent({
  open = false,
  children,
  className,
}: {
  open?: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  if (!open) return null;
  return <div className={cn("pb-4", className)}>{children}</div>;
}
