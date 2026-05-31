"use client";

import { DigestBanner } from "@/components/dashboard/DigestBanner";
import { EmptyDashboard } from "@/components/dashboard/EmptyDashboard";
import { Skeleton } from "@/components/ui/skeleton";
import { useConnectedAccounts, useDigest } from "@/lib/queries/dashboard";

export default function DigestPage() {
  const accounts = useConnectedAccounts();
  const digest = useDigest();

  if (accounts.isLoading) {
    return (
      <main className="p-6">
        <Skeleton className="h-[188px] w-full" />
      </main>
    );
  }

  const connectedAccounts = accounts.data?.filter((a) => !a.disconnected_at) ?? [];
  if (connectedAccounts.length === 0) {
    return <EmptyDashboard />;
  }

  return (
    <main className="space-y-6 p-6">
      <h1 className="text-2xl font-semibold">Daily Digest</h1>
      <DigestBanner digest={digest.data} />
    </main>
  );
}
