import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import UpdatePasswordPage from "@/app/(auth)/auth/update-password/page";

const mockUpdateUser = vi.fn();

vi.mock("@/lib/supabase/client", () => ({
  createBrowserSupabaseClient: () => ({
    auth: { updateUser: mockUpdateUser },
  }),
}));

const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
}));

describe("UpdatePasswordPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders new password and confirm fields", () => {
    render(<UpdatePasswordPage />);
    expect(screen.getByLabelText("New password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm new password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Set password" })).toBeInTheDocument();
  });

  it("shows error without calling Supabase when passwords do not match", () => {
    render(<UpdatePasswordPage />);
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "abc123" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "xyz999" } });
    fireEvent.click(screen.getByRole("button", { name: "Set password" }));

    expect(screen.getByText("Passwords do not match.")).toBeInTheDocument();
    expect(mockUpdateUser).not.toHaveBeenCalled();
  });

  it("calls updateUser and redirects to / on success", async () => {
    mockUpdateUser.mockResolvedValueOnce({ error: null });
    render(<UpdatePasswordPage />);
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "newpass123" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "newpass123" } });
    fireEvent.click(screen.getByRole("button", { name: "Set password" }));

    await waitFor(() => {
      expect(mockUpdateUser).toHaveBeenCalledWith({ password: "newpass123" });
      expect(mockReplace).toHaveBeenCalledWith("/");
    });
  });

  it("shows Supabase error message on failure", async () => {
    mockUpdateUser.mockResolvedValueOnce({ error: { message: "Token expired" } });
    render(<UpdatePasswordPage />);
    fireEvent.change(screen.getByLabelText("New password"), { target: { value: "newpass123" } });
    fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "newpass123" } });
    fireEvent.click(screen.getByRole("button", { name: "Set password" }));

    await waitFor(() => {
      expect(screen.getByText("Token expired")).toBeInTheDocument();
    });
    expect(mockReplace).not.toHaveBeenCalled();
  });
});
