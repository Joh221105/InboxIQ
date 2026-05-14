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

export function useUpdateContext() {
  const queryClient = useQueryClient();

  function pollJob(jobId: string, context: ContextValue) {
    const check = () => {
      void apiFetch<JobStatus>(`/jobs/${jobId}`)
        .then((job) => {
          if (job.status === "running") return;
          window.clearInterval(timer);
          if (job.status === "done") {
            toast.success(`Done - your inbox now reflects ${context}`);
            void queryClient.invalidateQueries({ queryKey: ["emails"] });
            void queryClient.invalidateQueries({ queryKey: ["digest"] });
            void queryClient.invalidateQueries({ queryKey: ["email-counts"] });
            void queryClient.invalidateQueries({ queryKey: ["emails-counts"] });
          } else {
            toast.error("Context switch failed");
          }
        })
        .catch(() => {
          window.clearInterval(timer);
          toast.error("Context switch failed");
        });
    };
    const timer = window.setInterval(check, 1500);
    check();
  }

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
    onSuccess: (data, context) => {
      queryClient.setQueryData(["user-context"], data.user);
      if (data.job_id) {
        toast.success("Re-triaging the last 100 emails...");
        pollJob(data.job_id, context);
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
