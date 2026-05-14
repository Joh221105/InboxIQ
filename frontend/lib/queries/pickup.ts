"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiFetch } from "@/lib/api";
import type { Email, PickupCodeList } from "@/types";

function pickupPath(used: boolean, includeExpired: boolean): string {
  const params = new URLSearchParams({
    used: String(used),
    include_expired: String(includeExpired),
  });
  return `/pickup-codes?${params.toString()}`;
}

export function useActivePickupCodes(includeExpired: boolean) {
  return useQuery({
    queryKey: ["pickup-codes", "active", includeExpired],
    queryFn: () => apiFetch<PickupCodeList>(pickupPath(false, includeExpired)),
    refetchInterval: 60_000,
    refetchIntervalInBackground: false,
  });
}

export function useUsedPickupCodes(enabled = false) {
  return useQuery({
    queryKey: ["pickup-codes", "used"],
    enabled,
    queryFn: () => apiFetch<PickupCodeList>(pickupPath(true, true)),
  });
}

export function useMarkPickupUsed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (emailId: string) =>
      apiFetch<Email>(`/emails/${emailId}`, {
        method: "PATCH",
        body: JSON.stringify({ pickup_used: true, is_archived: true }),
      }),
    onMutate: async (emailId) => {
      await queryClient.cancelQueries({ queryKey: ["pickup-codes", "active"] });
      await queryClient.cancelQueries({ queryKey: ["pickup-codes", "used"] });
      const previous = queryClient.getQueriesData<PickupCodeList>({ queryKey: ["pickup-codes", "active"] });
      const previousUsed = queryClient.getQueryData<PickupCodeList>(["pickup-codes", "used"]);
      const moved = previous.flatMap(([, data]) => data?.items.filter((item) => item.email_id === emailId) ?? []);

      for (const [queryKey, data] of previous) {
        if (!data) continue;
        queryClient.setQueryData<PickupCodeList>(queryKey, {
          ...data,
          items: data.items.filter((item) => item.email_id !== emailId),
        });
      }

      if (moved.length > 0) {
        queryClient.setQueryData<PickupCodeList>(["pickup-codes", "used"], {
          items: [
            ...moved.map((item) => ({ ...item, pickup_used_at: new Date().toISOString() })),
            ...(previousUsed?.items ?? []),
          ],
        });
      }

      return { previous, previousUsed };
    },
    onError: (_error, _emailId, context) => {
      for (const [queryKey, data] of context?.previous ?? []) {
        queryClient.setQueryData(queryKey, data);
      }
      queryClient.setQueryData(["pickup-codes", "used"], context?.previousUsed);
      toast.error("Could not mark code as used");
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["pickup-codes"] });
      void queryClient.invalidateQueries({ queryKey: ["emails"] });
      void queryClient.invalidateQueries({ queryKey: ["email-counts"] });
    },
  });
}
