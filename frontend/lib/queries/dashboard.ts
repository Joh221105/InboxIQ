"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { ConnectedAccount, Digest, EmailListPage, PickupCodeList, User } from "@/types";

function isoDate(offsetDays: number): string {
  const date = new Date();
  date.setHours(0, 0, 0, 0);
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().slice(0, 10);
}

export function useDigest() {
  return useQuery({
    queryKey: ["digest"],
    queryFn: () => apiFetch<Digest>("/digest/today"),
    refetchInterval: (query) => {
      const data = query.state.data;
      return !data ? 5000 : false;
    },
    refetchIntervalInBackground: false,
  });
}

export function useUpcomingDeadlines() {
  const params = new URLSearchParams({
    has_deadline: "true",
    deadline_after: isoDate(0),
    deadline_before: isoDate(7),
    order: "deadline_asc",
    limit: "10",
  });

  return useQuery({
    queryKey: ["emails", "upcoming-deadlines", params.toString()],
    queryFn: () => apiFetch<EmailListPage>(`/emails?${params.toString()}`),
    refetchInterval: 60_000,
    refetchIntervalInBackground: false,
  });
}

export function usePickupCodes() {
  return useQuery({
    queryKey: ["pickup-codes", "active", false],
    queryFn: () => apiFetch<PickupCodeList>("/pickup-codes?used=false&include_expired=false"),
    refetchInterval: 60_000,
    refetchIntervalInBackground: false,
  });
}

export function useUserContext() {
  return useQuery({
    queryKey: ["user-context"],
    queryFn: () => apiFetch<User>("/users/me"),
  });
}

export function useConnectedAccounts() {
  return useQuery({
    queryKey: ["connected-accounts"],
    queryFn: () => apiFetch<ConnectedAccount[]>("/accounts"),
  });
}
