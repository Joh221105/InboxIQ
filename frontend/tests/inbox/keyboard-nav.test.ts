import { describe, expect, it, vi } from "vitest";

import { getNextSelectedEmailId, shouldSkipInboxShortcut } from "@/components/inbox/use-email-keyboard-nav";
import type { Email } from "@/types";

const emails = [
  { id: "one" },
  { id: "two" },
  { id: "three" },
] as Email[];

describe("keyboard navigation helpers", () => {
  it("moves selection down and up", () => {
    expect(getNextSelectedEmailId(emails, "one", "down")).toBe("two");
    expect(getNextSelectedEmailId(emails, "two", "up")).toBe("one");
  });

  it("clamps at list boundaries", () => {
    expect(getNextSelectedEmailId(emails, "three", "down")).toBe("three");
    expect(getNextSelectedEmailId(emails, "one", "up")).toBe("one");
  });

  it("starts at the first email when nothing is selected", () => {
    expect(getNextSelectedEmailId(emails, null, "down")).toBe("one");
  });

  it("skips shortcuts when text input is focused", () => {
    const input = document.createElement("input");
    expect(shouldSkipInboxShortcut(input)).toBe(true);
    expect(shouldSkipInboxShortcut(document.createElement("button"))).toBe(false);
  });
});
