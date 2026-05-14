import { MapPinIcon } from "lucide-react";

import { ExpiryBadge } from "@/components/packages/ExpiryBadge";
import { RetailerLogo } from "@/components/packages/RetailerLogo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import type { PickupCode } from "@/types";

function parseExpiry(value: string | null): Date | null {
  return value ? new Date(`${value}T23:59:59`) : null;
}

function retailerName(code: PickupCode): string {
  if (code.retailer) return code.retailer;
  const domain = code.sender_email?.split("@")[1] ?? "";
  return domain || "Package";
}

export function PickupCodeCard({
  code,
  onMarkUsed,
  pending = false,
}: {
  code: PickupCode;
  onMarkUsed: (emailId: string) => void;
  pending?: boolean;
}) {
  const expiry = parseExpiry(code.pickup_expiry);

  return (
    <Card className="relative rounded-lg transition hover:scale-[1.02]" data-testid="pickup-code-card">
      <div className="absolute right-4 top-4">
        <ExpiryBadge expiry={expiry} />
      </div>
      <CardHeader className="pr-28">
        <div className="flex min-w-0 items-center gap-3">
          <RetailerLogo retailer={code.retailer} senderEmail={code.sender_email} />
          <CardTitle className="truncate whitespace-nowrap">{retailerName(code)}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="font-mono tabular-nums tracking-wider text-3xl font-bold whitespace-nowrap">
          {code.pickup_code}
        </div>
        <div className="min-h-10 space-y-1 text-sm text-muted-foreground">
          {code.locker_location ? (
            <div className="flex items-center gap-1.5 whitespace-nowrap">
              <MapPinIcon className="size-4 shrink-0" />
              <span className="truncate">{code.locker_location}</span>
            </div>
          ) : null}
          {expiry ? <div className="whitespace-nowrap">Expires {expiry.toLocaleDateString()}</div> : null}
        </div>
      </CardContent>
      <CardFooter>
        <Button className="w-full" onClick={() => onMarkUsed(code.email_id)} disabled={pending}>
          Mark as Used
        </Button>
      </CardFooter>
    </Card>
  );
}
