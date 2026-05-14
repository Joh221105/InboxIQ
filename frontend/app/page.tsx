"use client";

import { ContextSwitcher } from "@/components/dashboard/ContextSwitcher";
import { DigestBanner } from "@/components/dashboard/DigestBanner";
import { EmptyDashboard } from "@/components/dashboard/EmptyDashboard";
import { PickupCodesStrip } from "@/components/dashboard/PickupCodesStrip";
import { UpcomingDeadlinesPanel } from "@/components/dashboard/UpcomingDeadlinesPanel";
import { Skeleton } from "@/components/ui/skeleton";
import { useUpdateContext } from "@/lib/queries/context-switch";
import {
  useConnectedAccounts,
  useDigest,
  usePickupCodes,
  useUpcomingDeadlines,
  useUserContext,
} from "@/lib/queries/dashboard";

function firstName(email: string | undefined): string {
  const local = email?.split("@")[0] ?? "there";
  const cleaned = local.split(/[._-]/)[0] ?? local;
  return cleaned ? cleaned.charAt(0).toUpperCase() + cleaned.slice(1) : "there";
}

function DashboardSkeleton() {
  return (
    <main className="space-y-6 p-6">
      <div className="flex items-center justify-between gap-4">
        <Skeleton className="h-9 w-56" />
        <Skeleton className="h-9 w-[30rem] max-w-full" />
      </div>
      <Skeleton className="h-[188px] w-full" />
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Skeleton className="h-[260px] w-full" />
        <Skeleton className="h-[260px] w-full" />
      </div>
    </main>
  );
}

export default function HomePage() {
  const user = useUserContext();
  const accounts = useConnectedAccounts();
  const digest = useDigest();
  const deadlines = useUpcomingDeadlines();
  const pickupCodes = usePickupCodes();
  const updateContext = useUpdateContext();

  const loadingShell = user.isLoading || accounts.isLoading;
  if (loadingShell) return <DashboardSkeleton />;

  const connectedAccounts = accounts.data?.filter((account) => !account.disconnected_at) ?? [];
  if (connectedAccounts.length === 0) return <EmptyDashboard />;

  const currentContext = user.data?.default_context ?? "Daily";

  return (
    <main className="space-y-6 p-6">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Good morning, {firstName(user.data?.email)}</h1>
          <p className="text-sm text-muted-foreground">Your inbox briefing is ready.</p>
        </div>
        <ContextSwitcher
          value={currentContext}
          loading={updateContext.isPending}
          onChange={(context) => updateContext.mutate(context)}
        />
      </header>

      <DigestBanner digest={digest.data} />

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <UpcomingDeadlinesPanel emails={deadlines.data?.items ?? []} />
        <PickupCodesStrip codes={pickupCodes.data?.items ?? []} />
      </section>
    </main>
  );
}
