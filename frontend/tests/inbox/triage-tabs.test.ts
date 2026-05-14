import { describe, expect, it } from "vitest";

import { emptyStateForTab } from "@/components/inbox/triage-tabs";

describe("emptyStateForTab", () => {
  it("returns correct empty text for all tab", () => {
    expect(emptyStateForTab("all")).toBe("No emails yet");
  });

  it("returns correct empty text for action_required tab", () => {
    expect(emptyStateForTab("action_required")).toBe("No urgent emails right now. Nice.");
  });

  it("returns correct empty text for worth_reading tab", () => {
    expect(emptyStateForTab("worth_reading")).toBe("Reading list is clear.");
  });

  it("returns correct empty text for auto_archive tab", () => {
    expect(emptyStateForTab("auto_archive")).toBe("Auto-archived emails will collect here.");
  });

  it("returns fallback for unknown tab values", () => {
    expect(emptyStateForTab("unknown_tab")).toBe("No emails yet");
  });
});
