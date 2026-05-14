import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { createElement } from "react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useUpdateContext } from "@/lib/queries/context-switch";
import { apiFetch, ApiError } from "@/lib/api";
import { toast } from "sonner";

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return {
    ...actual,
    apiFetch: vi.fn(),
  };
});

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const user = {
  id: "user-1",
  email: "user@example.com",
  default_context: "Daily" as const,
  created_at: "2026-05-14T12:00:00Z",
};

function wrapperFor(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

beforeEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
});

describe("useUpdateContext", () => {
  it("polls a returned job and invalidates dashboard queries when done", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");
    queryClient.setQueryData(["user-context"], user);

    vi.mocked(apiFetch)
      .mockResolvedValueOnce({
        user: { ...user, default_context: "Job Hunting" },
        job_id: "job-1",
        total: 12,
      })
      .mockResolvedValueOnce({ status: "done", processed: 12, total: 12 });

    const { result } = renderHook(() => useUpdateContext(), { wrapper: wrapperFor(queryClient) });

    result.current.mutate("Job Hunting");
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/users/me/context", expect.any(Object)));

    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/jobs/job-1"));
    await waitFor(() =>
      expect(toast.success).toHaveBeenCalledWith("Done - your inbox now reflects Job Hunting"),
    );
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["emails"] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["digest"] });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ["email-counts"] });
  });

  it("rolls back optimistic context and shows a rate-limit toast on 429", async () => {
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    queryClient.setQueryData(["user-context"], user);
    vi.mocked(apiFetch).mockRejectedValueOnce(new ApiError(429, "rate_limited", "Too many requests"));

    const { result } = renderHook(() => useUpdateContext(), { wrapper: wrapperFor(queryClient) });

    result.current.mutate("Shopping");

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Just a moment - please wait before switching again."),
    );
    expect(queryClient.getQueryData(["user-context"])).toEqual(user);
  });
});
