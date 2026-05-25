"use client";

import { format } from "date-fns";

import { RetailerLogo } from "@/components/packages/RetailerLogo";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useMarkPickupUsed } from "@/lib/queries/pickup";
import type { PickupCode } from "@/types";

function retailerName(code: PickupCode): string {
  if (code.retailer) return code.retailer;
  return code.sender_email?.split("@")[1] ?? "Package";
}

function expiryLabel(expiry: string | null): string {
  if (!expiry) return "No expiry";
  return `Expires ${format(new Date(`${expiry}T00:00:00`), "MMM d")}`;
}

export function PickupCodesStrip({ codes }: { codes: PickupCode[] }) {
  const markUsed = useMarkPickupUsed();

  return (
    <Card className="min-h-[260px] p-5">
      <h2 className="mb-4 text-base font-semibold">Pickup Codes</h2>
      {codes.length === 0 ? (
        <div className="text-sm text-muted-foreground">No active codes</div>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-1 md:flex-wrap md:overflow-visible">
          {codes.map((code) => (
            <div
              key={code.email_id}
              className="grid min-w-[168px] gap-3 rounded-md border p-3"
            >
              <div className="flex min-w-0 items-center gap-2">
                <RetailerLogo
                  retailer={code.retailer}
                  senderEmail={code.sender_email}
                  className="size-6 shrink-0"
                />
                <span className="truncate text-sm font-medium">{retailerName(code)}</span>
              </div>
              <div>
                <div className="truncate font-mono text-lg font-semibold">{code.pickup_code}</div>
                <div className="text-xs text-muted-foreground">{expiryLabel(code.pickup_expiry)}</div>
              </div>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={markUsed.isPending && markUsed.variables === code.email_id}
                aria-label={`Mark ${retailerName(code)} pickup code ${code.pickup_code} as used`}
                onClick={() => markUsed.mutate(code.email_id)}
              >
                Mark used
              </Button>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
