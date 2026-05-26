import { test, expect } from "@playwright/test";

test.use({ storageState: "tests/e2e/storage-state.json" });

test("unified inbox happy path", async ({ page }) => {
  await page.route("**/emails**", async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === "/emails/counts") {
      await route.fulfill({
        json: {
          all: 1,
          action_required: 1,
          worth_reading: 0,
          auto_archive: 0,
        },
      });
      return;
    }
    if (url.pathname === "/emails/email-1/body") {
      await route.fulfill({ json: { body_html: "<p>Reply by Friday.</p>" } });
      return;
    }
    if (url.pathname === "/emails/email-1") {
      await route.fulfill({
        json: {
          id: "email-1",
          user_id: "user-1",
          account_id: "account-1",
          gmail_id: "gmail-1",
          thread_id: null,
          subject: "Interview deadline",
          sender: "recruiter@example.com",
          sender_name: "Recruiter",
          received_at: "2026-05-14T12:00:00Z",
          is_read: true,
          labels: [],
          ai_summary: "Reply by Friday.",
          ai_category: "action_required",
          triage_category: "action_required",
          deadline_extracted: "2026-05-16",
          action_items: ["Reply to recruiter"],
          ai_processed: true,
          pickup_used: false,
          is_archived: true,
          account_color: "#2563eb",
          account_email: "alex@example.com",
          created_at: "2026-05-14T12:00:00Z",
        },
      });
      return;
    }
    const category = url.searchParams.get("triage_category");
    await route.fulfill({
      json: {
        items:
          category === null || category === "action_required"
            ? [
                {
                  id: "email-1",
                  user_id: "user-1",
                  account_id: "account-1",
                  gmail_id: "gmail-1",
                  thread_id: null,
                  subject: "Interview deadline",
                  sender: "recruiter@example.com",
                  sender_name: "Recruiter",
                  received_at: "2026-05-14T12:00:00Z",
                  is_read: false,
                  labels: [],
                  ai_summary: "Reply by Friday.",
                  ai_category: "action_required",
                  triage_category: "action_required",
                  deadline_extracted: "2026-05-16",
                  action_items: ["Reply to recruiter"],
                  ai_processed: true,
                  pickup_used: false,
                  is_archived: false,
                  account_color: "#2563eb",
                  account_email: "alex@example.com",
                  created_at: "2026-05-14T12:00:00Z",
                },
              ]
            : [],
        next_cursor: null,
      },
    });
  });

  await page.goto("/inbox");
  await expect(page.getByTestId("email-card").first()).toBeVisible();

  await page.getByTestId("email-card").first().click();
  await expect(page.getByRole("dialog")).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();

  await page.getByRole("tab", { name: /Action Required/i }).click();
  await expect(page).toHaveURL(/tab=action_required/);

  await page.keyboard.press("e");
  await expect(page.getByTestId("email-card").first()).toBeVisible();
});
