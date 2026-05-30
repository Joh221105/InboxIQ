"use client";

import { useState } from "react";

import { PickupCodeCard } from "@/components/packages/PickupCodeCard";
import { UsedCodesSection } from "@/components/packages/UsedCodesSection";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useActivePickupCodes, useMarkPickupUsed } from "@/lib/queries/pickup";

export default function PackagesPage() {
  const [includeExpired, setIncludeExpired] = useState(false);
  const [usedOpen, setUsedOpen] = useState(false);
  const activeCodes = useActivePickupCodes(includeExpired);
  const markUsed = useMarkPickupUsed();
  const items = activeCodes.data?.items ?? [];

  return (
    <main className="space-y-8 p-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold whitespace-nowrap">Package Tracker</h1>
          <Badge className="whitespace-nowrap">{items.length} active</Badge>
        </div>
        <Label className="flex items-center gap-2 text-sm whitespace-nowrap">
          Show expired
          <Switch checked={includeExpired} onCheckedChange={setIncludeExpired} aria-label="Show expired" />
        </Label>
      </header>

      {activeCodes.isLoading ? (
        <div className="text-sm text-muted-foreground">Loading pickup codes...</div>
      ) : items.length > 0 ? (
        <section className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((code) => (
            <PickupCodeCard
              key={code.email_id}
              code={code}
              onMarkUsed={(emailId) => markUsed.mutate(emailId)}
              pending={markUsed.isPending && markUsed.variables === code.email_id}
            />
          ))}
        </section>
      ) : (
        <section className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
          No active pickup codes. We&apos;ll detect them automatically from your inbox.
        </section>
      )}

      <UsedCodesSection open={usedOpen} onOpenChange={setUsedOpen} />
    </main>
  );
}
