import { PackageIcon } from "lucide-react";

import { AmazonLogo } from "@/components/packages/logos/amazon-logo";
import { DhlLogo } from "@/components/packages/logos/dhl-logo";
import { FedExLogo } from "@/components/packages/logos/fedex-logo";
import { UpsLogo } from "@/components/packages/logos/ups-logo";
import { UspsLogo } from "@/components/packages/logos/usps-logo";

type Retailer = "amazon" | "fedex" | "ups" | "usps" | "dhl";

function normalizeRetailer(value: string | null | undefined): Retailer | null {
  const lower = value?.toLowerCase() ?? "";
  if (lower.includes("amazon")) return "amazon";
  if (lower.includes("fedex") || lower.includes("fed ex")) return "fedex";
  if (lower.includes("ups")) return "ups";
  if (lower.includes("usps") || lower.includes("postal")) return "usps";
  if (lower.includes("dhl")) return "dhl";
  return null;
}

function retailerFromEmail(senderEmail: string | null | undefined): Retailer | null {
  const domain = senderEmail?.split("@")[1]?.toLowerCase() ?? "";
  if (!domain) return null;
  if (domain === "amazon.com" || domain.startsWith("amazon.") || domain.includes(".amazon.")) return "amazon";
  if (domain.includes("fedex.")) return "fedex";
  if (domain.includes("ups.")) return "ups";
  if (domain.includes("usps.")) return "usps";
  if (domain.includes("dhl.")) return "dhl";
  return null;
}

export function resolveRetailer(retailer?: string | null, senderEmail?: string | null): Retailer | null {
  return normalizeRetailer(retailer) ?? retailerFromEmail(senderEmail);
}

export function RetailerLogo({
  retailer,
  senderEmail,
  className = "size-8",
}: {
  retailer?: string | null;
  senderEmail?: string | null;
  className?: string;
}) {
  const resolved = resolveRetailer(retailer, senderEmail);
  if (resolved === "amazon") return <AmazonLogo className={className} />;
  if (resolved === "fedex") return <FedExLogo className={className} />;
  if (resolved === "ups") return <UpsLogo className={className} />;
  if (resolved === "usps") return <UspsLogo className={className} />;
  if (resolved === "dhl") return <DhlLogo className={className} />;
  return <PackageIcon aria-label="Package" className={className} />;
}
