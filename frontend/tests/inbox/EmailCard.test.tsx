import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EmailCard } from "@/components/inbox/email-card";
import type { Email } from "@/types";

const baseEmail: Email = {
  id: "email-1",
  user_id: "user-1",
  account_id: "account-1",
  gmail_id: "gmail-1",
  thread_id: null,
  subject: "Interview update",
  sender: "recruiter@example.com",
  sender_name: "Recruiter Team",
  received_at: "2026-05-10T12:00:00Z",
  is_read: false,
  labels: [],
  ai_summary: "Reply to schedule the interview.",
  ai_category: null,
  triage_category: null,
  deadline_extracted: null,
  action_items: [],
  ai_processed: true,
  is_archived: false,
  account_color: "#2563eb",
  account_email: "me@example.com",
  created_at: "2026-05-10T12:00:00Z",
};

function renderCard(email: Email) {
  return render(
    <EmailCard
      email={email}
      selected={false}
      onClick={vi.fn()}
      onArchive={vi.fn()}
    />,
  );
}

describe("EmailCard", () => {
  it("renders action required email with deadline and contact tag", () => {
    const { getByTestId } = renderCard({
      ...baseEmail,
      triage_category: "action_required",
      deadline_extracted: "2026-11-15",
      contact_tag: { label: "Recruiter", color: "#dbeafe" },
    });

    expect(screen.getByText("Recruiter")).toBeInTheDocument();
    expect(screen.getByText("Recruiter Team")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /manage contact tag/i })).toHaveAttribute(
      "href",
      "/contacts?identifier=recruiter%40example.com",
    );
    expect(screen.getByText("Due Nov 15")).toBeInTheDocument();
    expect(screen.getByText("Triage category: Action required")).toBeInTheDocument();
    const card = getByTestId("email-card");
    expect(card).toHaveStyle({ borderLeftColor: "#dbeafe" });
  });

  it("falls back to the triage color when the contact tag has no color", () => {
    const { getByTestId } = renderCard({
      ...baseEmail,
      triage_category: "action_required",
      contact_tag: { label: "X", color: "" },
    });
    expect(getByTestId("email-card").getAttribute("style")).toContain("--triage-action");
  });

  it("renders worth reading without optional badges", () => {
    renderCard({ ...baseEmail, triage_category: "worth_reading" });

    expect(screen.getByText("Triage category: Worth reading")).toBeInTheDocument();
    expect(screen.queryByText("Due Nov 15")).not.toBeInTheDocument();
    expect(screen.queryByText("Recruiter")).not.toBeInTheDocument();
  });

  it("renders auto archive as faded", () => {
    const { getByTestId } = renderCard({ ...baseEmail, triage_category: "auto_archive" });

    expect(getByTestId("email-card")).toHaveClass("opacity-50");
    expect(screen.getByText("Triage category: Auto archive")).toBeInTheDocument();
  });

  it("renders AI processing placeholder and no triage badge for null category", () => {
    renderCard({
      ...baseEmail,
      ai_summary: null,
      ai_processed: false,
      triage_category: null,
      ai_category: null,
    });

    expect(screen.getByText("Summarizing")).toBeInTheDocument();
    expect(screen.queryByText(/Triage category:/)).not.toBeInTheDocument();
  });
});
