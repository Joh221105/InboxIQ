import { expect, test } from "@playwright/test";

const activeCode = {
  email_id: "email-active",
  pickup_code: "123456",
  pickup_expiry: "2026-05-15",
  pickup_used_at: null,
  retailer: "Amazon",
  locker_location: "Pine Hub Locker",
  sender_email: "locker@amazon.com",
  subject: "Your Amazon Locker pickup code",
  received_at: "2026-05-14T12:00:00Z",
};

test("package tracker happy path", async ({ page }) => {
  let used = false;

  await page.route("**/pickup-codes**", async (route) => {
    const url = new URL(route.request().url());
    const wantsUsed = url.searchParams.get("used") === "true";
    const items = wantsUsed ? (used ? [activeCode] : []) : used ? [] : [activeCode];
    await route.fulfill({ json: { items } });
  });

  await page.route("**/emails/email-active**", async (route) => {
    used = true;
    await route.fulfill({
      json: {
        id: "email-active",
        user_id: "user-1",
        account_id: "account-1",
        gmail_id: "gmail-1",
        thread_id: null,
        subject: activeCode.subject,
        sender: activeCode.sender_email,
        received_at: activeCode.received_at,
        is_read: false,
        labels: [],
        ai_summary: null,
        ai_category: "action_required",
        triage_category: "action_required",
        deadline_extracted: null,
        action_items: [],
        ai_processed: true,
        pickup_used: true,
        pickup_used_at: "2026-05-14T12:05:00Z",
        is_archived: true,
        account_color: "#2563eb",
        account_email: "me@example.com",
        created_at: activeCode.received_at,
      },
    });
  });

  await page.goto("/packages");
  await expect(page.getByText("123456")).toBeVisible();

  await page.getByRole("button", { name: /mark as used/i }).click();
  await expect(page.getByTestId("pickup-code-card")).toHaveCount(0);

  await page.getByRole("button", { name: /used codes/i }).click();
  await expect(page.getByText("123456")).toBeVisible();

  await page.reload();
  await expect(page.getByTestId("pickup-code-card")).toHaveCount(0);
  await page.getByRole("button", { name: /used codes/i }).click();
  await expect(page.getByText("123456")).toBeVisible();
});
