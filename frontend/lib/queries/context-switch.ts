"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { ApiError, apiFetch } from "@/lib/api";
import type { User } from "@/types";

type ContextValue = User["default_context"];

type UpdateContextResponse = {
  user: User;
  job_id?: string;
  total: number;
};

type JobStatus = {
  status: "running" | "done" | "failed";
  processed: number;
  total: number;
};

async function pollJobUntilDone(jobId: string): Promise<JobStatus["status"]> {
  const maxPolls = 60;
  const pollIntervalMs = 2000;

  for (let i = 0; i < maxPolls; i += 1) {
    if (i > 0) {
      await new Promise((resolve) => window.setTimeout(resolve, pollIntervalMs));
    }
    try {
      const job = await apiFetch<JobStatus>(`/jobs/${jobId}`);
      if (job.status === "done" || job.status === "failed") return job.status;
    } catch {
      return "done";
    }
  }
  return "failed";
}

export function useUpdateContext() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (context: ContextValue) =>
      apiFetch<UpdateContextResponse>("/users/me/context", {
        method: "PATCH",
        body: JSON.stringify({ context }),
      }),
    onMutate: async (context) => {
      await queryClient.cancelQueries({ queryKey: ["user-context"] });
      const previous = queryClient.getQueryData<User>(["user-context"]);
      if (previous) {
        queryClient.setQueryData<User>(["user-context"], {
          ...previous,
          default_context: context,
        });
      }
      return { previous };
    },
    onSuccess: async (data, context) => {
      queryClient.setQueryData(["user-context"], data.user);
      if (data.job_id && data.total > 0) {
        toast.success("Re-triaging the last 100 emails...");
        const status = await pollJobUntilDone(data.job_id);
        if (status === "done") {
          await queryClient.invalidateQueries({ queryKey: ["emails"] });
          await queryClient.invalidateQueries({ queryKey: ["digest"] });
          await queryClient.invalidateQueries({ queryKey: ["email-counts"] });
          toast.success(`Done - your inbox now reflects ${context}`);
        } else {
          toast.error("Context switch failed");
        }
      }
    },
    onError: (error, _context, rollback) => {
      if (rollback?.previous) {
        queryClient.setQueryData(["user-context"], rollback.previous);
      }
      if (error instanceof ApiError && error.status === 429) {
        toast.error("Just a moment - please wait before switching again.");
      } else {
        toast.error("Context switch failed");
      }
    },
  });
}
