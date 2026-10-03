import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ExpiryBadge } from "@/components/packages/expiry-badge";
import { PickupCodeCard } from "@/components/packages/pickup-code-card";
import type { PickupCode } from "@/types";

const baseCode: PickupCode = {
  email_id: "email-1",
  pickup_code: "123456",
  pickup_expiry: "2026-05-15",
  pickup_used_at: null,
  retailer: "Amazon",
  locker_location: "Pine Hub Locker",
  sender_email: "locker@amazon.com",
  subject: "Your pickup code",
  received_at: "2026-05-14T12:00:00Z",
};

describe("PickupCodeCard", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-05-14T12:00:00Z"));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders the code as large monospace text", () => {
    render(<PickupCodeCard code={baseCode} onMarkUsed={vi.fn()} />);

    expect(screen.getByText("123456")).toHaveClass("font-mono", "font-bold");
  });

  it("renders expiry badge state transitions", () => {
    const { rerender, container } = render(<ExpiryBadge expiry={null} />);
    expect(container).toBeEmptyDOMElement();

    rerender(<ExpiryBadge expiry={new Date("2026-05-13T12:00:00Z")} />);
    expect(screen.getByText("Expired")).toHaveClass("bg-red-50");

    rerender(<ExpiryBadge expiry={new Date("2026-05-15T00:00:00Z")} />);
    expect(screen.getByText("Expires in 12h")).toHaveClass("animate-pulse");

    rerender(<ExpiryBadge expiry={new Date("2026-05-16T12:00:00Z")} />);
    expect(screen.getByText("Expires Sat")).toHaveClass("bg-amber-50");

    rerender(<ExpiryBadge expiry={new Date("2026-05-20T12:00:00Z")} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("calls the mark-used handler", () => {
    const onMarkUsed = vi.fn();
    render(<PickupCodeCard code={baseCode} onMarkUsed={onMarkUsed} />);

    fireEvent.click(screen.getByRole("button", { name: /mark as used/i }));

    expect(onMarkUsed).toHaveBeenCalledWith("email-1");
  });

  it("shows 'Expires soon' (not 'Expired') for a same-day expiry", () => {
    render(<PickupCodeCard code={{ ...baseCode, pickup_expiry: "2026-05-14" }} onMarkUsed={vi.fn()} />);

    expect(screen.getByText("Expires soon")).toBeInTheDocument();
    expect(screen.queryByText("Expired")).not.toBeInTheDocument();
  });
});
