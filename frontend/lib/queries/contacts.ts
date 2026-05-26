"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiFetch } from "@/lib/api";
import type { ContactsGrouped, CreateContactRequest, CreateContactResponse, EmailListPage } from "@/types";

export function useContacts() {
  return useQuery({
    queryKey: ["contacts"],
    queryFn: () => apiFetch<ContactsGrouped>("/contacts"),
  });
}

export function useContactEmailHistory(contactTagId: string | null) {
  return useQuery({
    queryKey: ["contact-history", contactTagId],
    enabled: Boolean(contactTagId),
    queryFn: async () => {
      const active = await apiFetch<EmailListPage>(
        `/emails?contact_tag_id=${contactTagId}&is_archived=false&limit=25`,
      );
      const archived = await apiFetch<EmailListPage>(
        `/emails?contact_tag_id=${contactTagId}&is_archived=true&limit=25`,
      );
      return {
        items: [...active.items, ...archived.items].sort((a, b) => {
          const left = a.received_at ? new Date(a.received_at).getTime() : 0;
          const right = b.received_at ? new Date(b.received_at).getTime() : 0;
          return right - left;
        }),
        next_cursor: null,
      } satisfies EmailListPage;
    },
  });
}

export function useCreateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateContactRequest) =>
      apiFetch<CreateContactResponse>("/contacts", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      if (data.job_id) {
        toast.info(`Tagging ${data.retroactive_count} past emails...`);
        pollContactJob(data.job_id, data.retroactive_count, queryClient);
      } else {
        if (data.retroactive_count > 0) {
          queryClient.invalidateQueries({ queryKey: ["emails"] });
        }
        toast.success(`Contact tagged (${data.retroactive_count} past emails updated)`);
      }
    },
    onError: (err: Error) => {
      toast.error(err.message ?? "Failed to create tag");
    },
  });
}

function pollContactJob(jobId: string, total: number, queryClient: ReturnType<typeof useQueryClient>) {
  const interval = setInterval(async () => {
    try {
      const status = await apiFetch<{ status: string; processed: number; total: number }>(
        `/contacts/jobs/${jobId}`
      );
      if (status.status === "done" || status.status === "failed") {
        clearInterval(interval);
        if (status.status === "done") {
          toast.success(`Tagged ${status.processed} past emails ✓`);
          queryClient.invalidateQueries({ queryKey: ["emails"] });
        } else {
          toast.error("Retroactive tagging failed");
        }
      }
    } catch {
      clearInterval(interval);
    }
  }, 2000);
}

export function useDeleteContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (tagId: string) =>
      apiFetch<void>(`/contacts/${tagId}`, { method: "DELETE" }),
    onMutate: async (tagId) => {
      await queryClient.cancelQueries({ queryKey: ["contacts"] });
      const previous = queryClient.getQueryData<ContactsGrouped>(["contacts"]);
      if (previous) {
        const updated = { ...previous } as ContactsGrouped;
        for (const group of ["professor", "friend", "recruiter", "custom"] as const) {
          updated[group] = updated[group].filter((t) => t.id !== tagId);
        }
        queryClient.setQueryData(["contacts"], updated);
      }
      return { previous };
    },
    onError: (_err, _id, ctx) => {
      if (ctx?.previous) queryClient.setQueryData(["contacts"], ctx.previous);
      toast.error("Failed to delete tag");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
}
