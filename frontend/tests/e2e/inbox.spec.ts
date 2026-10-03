import { test, expect } from "@playwright/test";

import { mockConnectedAccount } from "./fixtures";

test.use({ storageState: "tests/e2e/storage-state.json" });

test("unified inbox supports preview, tabs, and accurate search filters", async ({ page }) => {
  const emails = [
    {
      id: "email-1",
      user_id: "user-1",
      account_id: "account-1",
      gmail_id: "gmail-1",
      thread_id: null,
      subject: "Interview loop details",
      sender: "recruiter@company.com",
      received_at: "2026-05-14T12:00:00Z",
      is_read: false,
      labels: [],
      ai_summary: "Schedule your onsite interview.",
      ai_category: "action_required",
      triage_category: "action_required",
      deadline_extracted: null,
      action_items: [],
      ai_processed: true,
      pickup_used: false,
      is_archived: false,
      account_color: "#2563eb",
      account_email: "alex@example.com",
      created_at: "2026-05-14T12:00:00Z",
    },
    {
      id: "email-2",
      user_id: "user-1",
      account_id: "account-1",
      gmail_id: "gmail-2",
      thread_id: null,
      subject: "Weekly grocery deals",
      sender: "newsletter@store.com",
      received_at: "2026-05-14T10:00:00Z",
      is_read: false,
      labels: [],
      ai_summary: "Promotional shopping newsletter.",
      ai_category: "auto_archive",
      triage_category: "auto_archive",
      deadline_extracted: null,
      action_items: [],
      ai_processed: true,
      pickup_used: false,
      is_archived: false,
      account_color: "#2563eb",
      account_email: "alex@example.com",
      created_at: "2026-05-14T10:00:00Z",
    },
  ];

  await page.route(/.*\/emails\/email-1\/body$/, async (route) => {
    await route.fulfill({ json: { body_html: "<p>Schedule your onsite interview.</p>" } });
  });

  await page.route(/.*\/emails.*/, async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/emails/counts") {
      await route.fulfill({
        json: { all: 2, action_required: 1, worth_reading: 0, auto_archive: 1 },
      });
      return;
    }
    const triage = url.searchParams.get("triage_category");
    const search = (url.searchParams.get("search") ?? "").toLowerCase();
    const senderSearch = (url.searchParams.get("sender_search") ?? "").toLowerCase();
    let filtered = emails;

    if (triage) {
      filtered = filtered.filter((email) => email.ai_category === triage);
    }
    if (search) {
      filtered = filtered.filter(
        (email) =>
          email.subject.toLowerCase().includes(search) ||
          email.sender.toLowerCase().includes(search),
      );
    }
    if (senderSearch) {
      filtered = filtered.filter((email) => email.sender.toLowerCase().includes(senderSearch));
    }

    await route.fulfill({ json: { items: filtered, next_cursor: null } });
  });

  await mockConnectedAccount(page);
  await page.goto("/inbox");
  // The All tab collapses auto-archived mail until the user asks to see it.
  await expect(page.getByTestId("email-card")).toHaveCount(1);
  await expect(page.getByText("1 auto-archived emails collapsed")).toBeVisible();
  await page.getByRole("button", { name: "Show auto-archived" }).click();
  await expect(page.getByTestId("email-card")).toHaveCount(2);

  await page.getByTestId("email-card").first().click();
  await expect(page.getByRole("dialog")).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();

  await page.keyboard.press("e");
  await expect(page.getByTestId("email-card").first()).toBeVisible();

  await page.getByLabel("Search emails").fill("interview");
  await expect(page.getByTestId("email-card")).toHaveCount(1);
  await expect(page.getByText("Interview loop details")).toBeVisible();

  await page.getByRole("button", { name: "By sender" }).click();
  await page.getByLabel("Search emails").fill("newsletter@store.com");
  await expect(page.getByTestId("email-card")).toHaveCount(1);
  await expect(page.getByText("Weekly grocery deals")).toBeVisible();
  await page.getByLabel("Search emails").fill("");

  await page.getByRole("tab", { name: /Action Required/i }).click();
  await expect(page).toHaveURL(/tab=action_required/);
  await expect(page.getByTestId("email-card")).toHaveCount(1);
  await expect(page.getByText("Interview loop details")).toBeVisible();
});
