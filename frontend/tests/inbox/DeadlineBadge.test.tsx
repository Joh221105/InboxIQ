import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DeadlineBadge } from "@/components/inbox/deadline-badge";

const TODAY = new Date("2026-05-13T10:00:00.000Z");

describe("DeadlineBadge", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(TODAY);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders nothing when date is null", () => {
    const { container } = render(<DeadlineBadge date={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when date is undefined", () => {
    const { container } = render(<DeadlineBadge date={undefined} />);
    expect(container.firstChild).toBeNull();
  });

  it("formats an upcoming deadline correctly", () => {
    render(<DeadlineBadge date="2026-05-20" />);
    expect(screen.getByText("Due May 20")).toBeInTheDocument();
  });

  it("shows overdue deadline with red styling", () => {
    render(<DeadlineBadge date="2026-05-10" />);
    const badge = screen.getByText("Due May 10");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("text-red-700");
  });

  it("shows near deadline (within 3 days) with amber styling", () => {
    render(<DeadlineBadge date="2026-05-14" />);
    const badge = screen.getByText("Due May 14");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("text-amber-800");
  });

  it("shows far deadline (more than 3 days) with muted styling", () => {
    render(<DeadlineBadge date="2026-06-01" />);
    const badge = screen.getByText("Due Jun 1");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("text-muted-foreground");
  });
});
