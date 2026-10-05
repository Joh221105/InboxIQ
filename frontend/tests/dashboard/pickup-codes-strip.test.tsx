import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PickupCodesStrip } from "@/components/dashboard/pickup-codes-strip";
import type { PickupCode } from "@/types";

const mutate = vi.fn();

vi.mock("@/lib/queries/pickup", () => ({
  useMarkPickupUsed: () => ({
    mutate,
    isPending: false,
    variables: undefined,
  }),
}));

const code: PickupCode = {
  email_id: "email-1",
  pickup_code: "ABC123",
  pickup_expiry: "2026-05-26",
  pickup_used_at: null,
  retailer: "Amazon",
  locker_location: "North Campus Locker",
  sender_email: "locker@amazon.com",
  subject: "Your package is ready",
  received_at: "2026-05-25T12:00:00Z",
};

describe("PickupCodesStrip", () => {
  beforeEach(() => {
    mutate.mockClear();
  });

  it("shows retailer, code, expiry, and marks a dashboard code as used", () => {
    render(<PickupCodesStrip codes={[code]} />);

    expect(screen.getByText("Amazon")).toBeInTheDocument();
    expect(screen.getByText("ABC123")).toBeInTheDocument();
    expect(screen.getByText("Expires May 26")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /mark amazon pickup code abc123 as used/i }));

    expect(mutate).toHaveBeenCalledWith("email-1");
  });
});
