import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DigestBanner } from "@/components/dashboard/DigestBanner";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("DigestBanner", () => {
  it("renders digest items", () => {
    render(
      <DigestBanner
        digest={{
          generated_at: "2026-05-14T16:00:00Z",
          context: "Job Hunting",
          degraded: false,
          items: [
            {
              summary: "Reply to recruiter about final interview by Friday.",
              source_email_id: "email-1",
              sender: "recruiter@example.com",
              deadline: "2026-05-15",
            },
          ],
        }}
      />,
    );

    expect(screen.getByText("Today's briefing")).toBeInTheDocument();
    expect(screen.getByText("Reply to recruiter about final")).toBeInTheDocument();
    expect(screen.getByText("interview by Friday.")).toBeInTheDocument();
    expect(screen.getByText(/recruiter@example.com/)).toBeInTheDocument();
    expect(screen.getByText("Due May 15")).toBeInTheDocument();
  });

  it("renders calm empty state when digest is empty and not degraded", () => {
    render(
      <DigestBanner
        digest={{
          generated_at: "2026-05-14T16:00:00Z",
          context: "Daily",
          degraded: false,
          items: [],
        }}
      />,
    );

    expect(screen.getByText("Inbox calm. Nothing urgent today.")).toBeInTheDocument();
  });

  it("shows degraded note", () => {
    render(
      <DigestBanner
        digest={{
          generated_at: "2026-05-14T16:00:00Z",
          context: "Shopping",
          degraded: true,
          items: [],
        }}
      />,
    );

    expect(screen.getByText("Live digest unavailable - showing recent action items")).toBeInTheDocument();
  });
});
