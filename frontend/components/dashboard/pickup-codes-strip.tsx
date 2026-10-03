"use client";

import { format } from "date-fns";
import { Clock } from "lucide-react";

import { RetailerLogo } from "@/components/packages/retailer-logo";
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

function isExpiringSoon(expiry: string | null): boolean {
  if (!expiry) return false;
  return new Date(`${expiry}T23:59:59`).getTime() - Date.now() < 24 * 60 * 60 * 1000;
}

export function PickupCodesStrip({ codes }: { codes: PickupCode[] }) {
  const markUsed = useMarkPickupUsed();

  return (
    <Card className="min-h-[260px] p-5">
      <h2 className="mb-4 text-base font-semibold">Pickup Codes</h2>
      {codes.length === 0 ? (
        <div className="text-sm text-muted-foreground">
          No active codes — Bun will detect them from your inbox.
        </div>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-1 md:flex-wrap md:overflow-visible">
          {codes.map((code) => {
            const soon = isExpiringSoon(code.pickup_expiry);
            return (
              <div
                key={code.email_id}
                className="grid min-w-[168px] gap-3 rounded-[var(--radius)] border p-3"
                style={{
                  background:  "var(--code-bg)",
                  borderColor: "var(--code-border)",
                }}
              >
                <div className="flex min-w-0 items-center gap-2">
                  <RetailerLogo
                    retailer={code.retailer}
                    senderEmail={code.sender_email}
                    className="size-6 shrink-0"
                  />
                  <span
                    className="truncate text-sm font-medium"
                    style={{ color: "var(--code-fg)" }}
                  >
                    {retailerName(code)}
                  </span>
                </div>

                <div className="text-center">
                  <div
                    className="font-mono text-[22px] font-bold tracking-[2px]"
                    style={{ color: "var(--code-fg)" }}
                  >
                    {code.pickup_code}
                  </div>
                  <div
                    className="mt-0.5 flex items-center justify-center gap-1 text-xs"
                    style={{ color: soon ? "var(--triage-read)" : "color-mix(in oklch, var(--code-fg) 65%, transparent)" }}
                  >
                    {soon && <Clock className="size-3" />}
                    {expiryLabel(code.pickup_expiry)}
                  </div>
                </div>

                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="w-full"
                  style={{
                    borderColor: "var(--code-border)",
                    color:       "var(--code-fg)",
                    background:  "transparent",
                  }}
                  disabled={markUsed.isPending && markUsed.variables === code.email_id}
                  aria-label={`Mark ${retailerName(code)} pickup code ${code.pickup_code} as used`}
                  onClick={() => markUsed.mutate(code.email_id)}
                >
                  Mark used
                </Button>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}
