import { MapPin, Clock, Check } from "lucide-react";

import { ExpiryBadge } from "@/components/packages/ExpiryBadge";
import { RetailerLogo } from "@/components/packages/RetailerLogo";
import { Button } from "@/components/ui/button";
import type { PickupCode } from "@/types";

function parseExpiry(value: string | null): Date | null {
  return value ? new Date(`${value}T23:59:59`) : null;
}

function retailerName(code: PickupCode): string {
  if (code.retailer) return code.retailer;
  const domain = code.sender_email?.split("@")[1] ?? "";
  return domain || "Package";
}

function isExpiringSoon(expiry: Date | null): boolean {
  if (!expiry) return false;
  return expiry.getTime() - Date.now() < 24 * 60 * 60 * 1000;
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
  const soon   = isExpiringSoon(expiry);

  return (
    <div
      className="flex flex-col gap-[14px] rounded-[var(--radius)] border p-5 transition-transform duration-150 hover:scale-[1.015]"
      style={{
        background:   "var(--code-bg)",
        borderColor:  "var(--code-border)",
        boxShadow:    "0 1px 3px oklch(0.40 0.03 60 / 0.07)",
      }}
      data-testid="pickup-code-card"
    >
      {/* header: retailer + expiry badge */}
      <div className="flex items-center gap-2">
        <RetailerLogo retailer={code.retailer} senderEmail={code.sender_email} />
        <span
          className="truncate text-[14px] font-medium"
          style={{ color: "var(--code-fg)" }}
        >
          {retailerName(code)}
        </span>
        {soon && (
          <span
            className="ml-auto flex shrink-0 items-center gap-1 rounded-full px-2.5 py-0.5 text-[12px] font-semibold"
            style={{
              background: "color-mix(in oklch, var(--triage-read) 18%, transparent)",
              color:      "var(--triage-read)",
            }}
          >
            <Clock className="size-[11px]" />
            Expires soon
          </span>
        )}
        {!soon && expiry && (
          <span className="ml-auto shrink-0">
            <ExpiryBadge expiry={expiry} />
          </span>
        )}
      </div>

      {/* pickup code — JetBrains Mono, large, centered */}
      <div
        className="text-center font-mono text-[28px] font-bold tracking-[3px]"
        style={{ color: "var(--code-fg)" }}
      >
        {code.pickup_code}
      </div>

      {/* location + expiry details */}
      <div className="text-center">
        {code.locker_location && (
          <div
            className="flex items-center justify-center gap-1.5 text-[13.5px] font-medium"
            style={{ color: "var(--code-fg)" }}
          >
            <MapPin className="size-[14px] shrink-0" />
            <span className="truncate">{code.locker_location}</span>
          </div>
        )}
        {expiry && (
          <div
            className="mt-1 text-[12px]"
            style={{ color: soon ? "var(--triage-read)" : "color-mix(in oklch, var(--code-fg) 70%, transparent)" }}
          >
            Expires {expiry.toLocaleDateString()}
          </div>
        )}
      </div>

      {/* action */}
      <Button
        variant="outline"
        className="w-full gap-2"
        style={{
          borderColor: "var(--code-border)",
          color:       "var(--code-fg)",
          background:  "transparent",
        }}
        onClick={() => onMarkUsed(code.email_id)}
        disabled={pending}
      >
        <Check className="size-4" />
        Mark as Used
      </Button>
    </div>
  );
}
