import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TriageBadge } from "@/components/inbox/triage-badge";
import type { TriageCategory } from "@/types";

describe("TriageBadge", () => {
  it.each<[TriageCategory, string]>([
    ["action_required", "Action required"],
    ["worth_reading", "Worth reading"],
    ["auto_archive", "Auto archive"],
  ])("renders correct label for %s", (category, label) => {
    render(<TriageBadge category={category} />);
    expect(screen.getByLabelText(`Triage category: ${label}`)).toBeInTheDocument();
  });

  it("renders nothing when category is null", () => {
    const { container } = render(<TriageBadge category={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when category is undefined", () => {
    const { container } = render(<TriageBadge category={undefined} />);
    expect(container.firstChild).toBeNull();
  });
});
