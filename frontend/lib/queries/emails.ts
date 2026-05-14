"use client";

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiFetch } from "@/lib/api";
import type { Email, EmailBody, EmailCounts, EmailListPage, TriageCategory } from "@/types";

type EmailQueryArgs = {
  category?: TriageCategory | "all";
  search?: string;
  senderSearch?: string;
  accountId?: string;
};

function buildEmailPath(args: EmailQueryArgs, cursor?: string | null): string {
  const params = new URLSearchParams();
  params.set("limit", "50");
  if (args.category && args.category !== "all") params.set("triage_category", args.category);
  if (args.search) params.set("search", args.search);
  if (args.senderSearch) params.set("sender_search", args.senderSearch);
  if (args.accountId) params.set("account_id", args.accountId);
  if (cursor) params.set("cursor", cursor);
  return `/emails?${params.toString()}`;
}

export function useEmails(args: EmailQueryArgs) {
  return useInfiniteQuery({
    queryKey: ["emails", args],
    initialPageParam: null as string | null,
    queryFn: ({ pageParam }) => apiFetch<EmailListPage>(buildEmailPath(args, pageParam)),
    getNextPageParam: (lastPage) => lastPage.next_cursor,
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });
}

export function useEmailCounts() {
  return useQuery({
    queryKey: ["email-counts"],
    queryFn: () => apiFetch<EmailCounts>("/emails/counts"),
    refetchInterval: 30_000,
    refetchIntervalInBackground: false,
  });
}

export function useEmailBody(emailId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: ["email-body", emailId],
    enabled: Boolean(emailId && enabled),
    queryFn: () => apiFetch<EmailBody>(`/emails/${emailId}/body`),
  });
}

export function useArchiveEmail() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (emailId: string) =>
      apiFetch<Email>(`/emails/${emailId}`, {
        method: "PATCH",
        body: JSON.stringify({ is_archived: true }),
      }),
    onMutate: async (emailId) => {
      await queryClient.cancelQueries({ queryKey: ["emails"] });
      const previous = queryClient.getQueriesData<{ pages: EmailListPage[] }>({
        queryKey: ["emails"],
      });

      for (const [queryKey, data] of previous) {
        if (!data?.pages) continue;
        queryClient.setQueryData(queryKey, {
          ...data,
          pages: data.pages.map((page) => ({
            ...page,
            items: page.items.filter((email) => email.id !== emailId),
          })),
        });
      }

      return { previous };
    },
    onError: (_error, _emailId, context) => {
      for (const [queryKey, data] of context?.previous ?? []) {
        queryClient.setQueryData(queryKey, data);
      }
      toast.error("Archive failed");
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: ["email-counts"] });
      void queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
}
