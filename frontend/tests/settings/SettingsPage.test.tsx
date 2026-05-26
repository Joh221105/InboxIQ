import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import SettingsPage from "@/app/settings/page";
import { apiFetch } from "@/lib/api";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

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
    info: vi.fn(),
  },
}));

const user = {
  id: "user-1",
  email: "user@example.com",
  default_context: "Daily" as const,
  notification_tag_preferences: { recruiter: true, friend: false },
  data_retention_days: 365,
  created_at: "2026-05-25T12:00:00Z",
};

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiFetch)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce(user);
  });

  it("renders context, notification, retention, and delete-data controls", async () => {
    render(<SettingsPage />);

    await waitFor(() => expect(screen.getByText("Default context")).toBeInTheDocument());

    expect(screen.getByRole("button", { name: "Daily" })).toBeInTheDocument();
    expect(screen.getByLabelText("Notify for Recruiter")).toBeChecked();
    expect(screen.getByLabelText("Notify for Friend")).not.toBeChecked();
    expect(screen.getByLabelText("Data retention days")).toHaveValue(365);
    expect(screen.getByRole("button", { name: "Delete stored email data" })).toBeInTheDocument();
  });
});
