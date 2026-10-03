"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiFetch } from "@/lib/api";
import type { ConnectedAccount, EmailDataDeleteCounts, User } from "@/types";

export type SettingsUpdate = {
  notification_tag_preferences: Record<string, boolean>;
  data_retention_days: number | null;
};

export function useDisconnectAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (account: ConnectedAccount) =>
      apiFetch<void>(`/accounts/${account.id}`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["connected-accounts"] }),
    onError: (_error, account) => toast.error(`Failed to disconnect ${account.email_address}`),
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (update: SettingsUpdate) =>
      apiFetch<User>("/users/me/settings", { method: "PATCH", body: JSON.stringify(update) }),
    onSuccess: (user) => {
      queryClient.setQueryData(["user-context"], user);
      toast.success("Settings saved");
    },
    onError: () => toast.error("Failed to save settings"),
  });
}

export function useDeleteEmailData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<EmailDataDeleteCounts>("/users/me/email-data", { method: "DELETE" }),
    onSuccess: (counts) => {
      toast.success(`Deleted ${counts.emails} emails and related AI records`);
      void queryClient.invalidateQueries();
    },
    onError: () => toast.error("Failed to delete stored email data"),
  });
}
