import { differenceInHours, format } from "date-fns";

import { Badge } from "@/components/ui/badge";

export function ExpiryBadge({ expiry }: { expiry: Date | null }) {
  if (!expiry) return null;

  const hours = differenceInHours(expiry, new Date());
  if (hours < 0) {
    return <Badge className="border-red-200 bg-red-50 text-red-700">Expired</Badge>;
  }
  if (hours <= 24) {
    return (
      <Badge className="animate-pulse border-red-200 bg-red-50 text-red-700">
        {hours > 0 ? `Expires in ${hours}h` : "Expires soon"}
      </Badge>
    );
  }
  if (hours <= 72) {
    return <Badge className="border-amber-200 bg-amber-50 text-amber-800">Expires {format(expiry, "EEE")}</Badge>;
  }
  return null;
}
