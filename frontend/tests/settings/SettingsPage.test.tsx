import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SettingsPage from "@/app/(app)/settings/page";
import { apiFetch } from "@/lib/api";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, apiFetch: vi.fn() };
});

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn(), info: vi.fn() } }));

const user = {
  id: "user-1",
  email: "user@example.com",
  default_context: "Daily" as const,
  notification_tag_preferences: { recruiter: true, friend: false },
  data_retention_days: 365,
  created_at: "2026-05-25T12:00:00Z",
};

function renderPage(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: RequestInit) => {
      if (path === "/accounts") return [];
      if (path === "/users/me") return user;
      if (path === "/users/me/settings" && init?.method === "PATCH") {
        return { ...user, ...JSON.parse(String(init.body)) };
      }
      throw new Error(`unexpected request ${path}`);
    });
  });

  it("renders notification and retention controls from the current user", async () => {
    renderPage(<SettingsPage />);

    expect(await screen.findByLabelText("Data retention days")).toHaveValue(365);
    expect(screen.getByLabelText("Notify for Recruiter")).toBeChecked();
    expect(screen.getByLabelText("Notify for Friend")).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Delete stored email data" })).toBeInTheDocument();
  });

  it("saves edited settings", async () => {
    renderPage(<SettingsPage />);

    await waitFor(() => expect(screen.getByLabelText("Data retention days")).toHaveValue(365));
    fireEvent.change(screen.getByLabelText("Data retention days"), { target: { value: "30" } });
    fireEvent.click(screen.getByRole("button", { name: "Save settings" }));

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/users/me/settings", {
        method: "PATCH",
        body: JSON.stringify({
          notification_tag_preferences: { recruiter: true, friend: false },
          data_retention_days: 30,
        }),
      }),
    );
  });

  it("tells the user when connected accounts fail to load", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path === "/users/me") return user;
      throw new Error("network down");
    });

    renderPage(<SettingsPage />);

    expect(await screen.findByText("Couldn't load connected accounts.")).toBeInTheDocument();
  });
});
