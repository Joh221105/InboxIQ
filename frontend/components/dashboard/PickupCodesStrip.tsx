"use client";

import { format, differenceInHours } from "date-fns";
import { useRouter } from "next/navigation";

import { RetailerLogo } from "@/components/packages/RetailerLogo";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { PickupCode } from "@/types";

function expiringSoon(expiry: string | null): boolean {
  if (!expiry) return false;
  const hours = differenceInHours(new Date(`${expiry}T23:59:59`), new Date());
  return hours >= 0 && hours < 24;
}

export function PickupCodesStrip({ codes }: { codes: PickupCode[] }) {
  const router = useRouter();

  return (
    <Card className="min-h-[260px] p-5">
      <h2 className="mb-4 text-base font-semibold">Pickup Codes</h2>
      {codes.length === 0 ? (
        <div className="text-sm text-muted-foreground">No active codes</div>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-1 md:flex-wrap md:overflow-visible">
          {codes.map((code) => (
            <button
              key={code.email_id}
              type="button"
              onClick={() => router.push("/packages")}
              className="flex min-w-[152px] items-center gap-2 rounded-md border p-3 text-left transition-colors hover:bg-accent"
            >
              <RetailerLogo
                retailer={code.retailer}
                senderEmail={code.sender_email}
                className="size-6 shrink-0"
              />
              <span className="min-w-0">
                <span className="block truncate font-mono text-sm font-semibold">{code.pickup_code}</span>
                {expiringSoon(code.pickup_expiry) && code.pickup_expiry ? (
                  <Badge className="mt-1 bg-amber-500 text-white hover:bg-amber-500">
                    Expires {format(new Date(`${code.pickup_expiry}T00:00:00`), "MMM d")}
                  </Badge>
                ) : null}
              </span>
            </button>
          ))}
        </div>
      )}
    </Card>
  );
}
