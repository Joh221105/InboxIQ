"use client";

import { formatDistanceToNow } from "date-fns";

import { RetailerLogo } from "@/components/packages/RetailerLogo";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { useUsedPickupCodes } from "@/lib/queries/pickup";

function markedText(usedAt: string | null): string {
  if (!usedAt) return "Marked used";
  return `Marked used ${formatDistanceToNow(new Date(usedAt))} ago`;
}

export function UsedCodesSection({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data, isLoading } = useUsedPickupCodes(open);
  const items = data?.items ?? [];

  if (!open && data && items.length === 0) return null;

  return (
    <Accordion open={open} onOpenChange={onOpenChange}>
      <AccordionItem>
        <AccordionTrigger>Used codes</AccordionTrigger>
        <AccordionContent>
          {isLoading ? <p className="text-sm text-muted-foreground">Loading used codes...</p> : null}
          <div className="divide-y">
            {items.map((item) => (
              <div key={item.email_id} className="flex items-center gap-3 py-3">
                <RetailerLogo retailer={item.retailer} senderEmail={item.sender_email} className="size-6" />
                <div className="min-w-0 flex-1">
                  <div className="truncate whitespace-nowrap text-sm font-medium">{item.retailer ?? item.sender_email ?? "Package"}</div>
                  <div className="font-mono text-sm whitespace-nowrap">{item.pickup_code}</div>
                </div>
                <div className="shrink-0 text-xs text-muted-foreground whitespace-nowrap">{markedText(item.pickup_used_at)}</div>
              </div>
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
