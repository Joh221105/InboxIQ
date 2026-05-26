import { expect, test } from "@playwright/test";

test.use({ storageState: "tests/e2e/storage-state.json" });

test("dashboard context switch refreshes digest", async ({ page }) => {
  let context = "Daily";
  let jobPolls = 0;

  await page.route("**/users/me", async (route) => {
    await route.fulfill({
      json: {
        id: "user-1",
        email: "alex@example.com",
        default_context: context,
        created_at: "2026-05-14T12:00:00Z",
      },
    });
  });

  await page.route("**/accounts", async (route) => {
    await route.fulfill({
      json: [
        {
          id: "account-1",
          email_address: "alex@example.com",
          provider: "gmail",
          color: "#2563eb",
          last_synced: "2026-05-14T12:00:00Z",
          disconnected_at: null,
        },
      ],
    });
  });

  await page.route("**/digest/today", async (route) => {
    await route.fulfill({
      json: {
        generated_at: "2026-05-14T16:00:00Z",
        context,
        degraded: false,
        items: [
          {
            summary:
              context === "Job Hunting"
                ? "Reply to recruiter about interview time."
                : "Review today's school application checklist.",
            source_email_id: "email-1",
            sender: "updates@example.com",
            deadline: "2026-05-16",
          },
        ],
      },
    });
  });

  await page.route("**/emails**", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            id: "email-1",
            user_id: "user-1",
            account_id: "account-1",
            gmail_id: "gmail-1",
            thread_id: null,
            subject: "Interview deadline",
            sender: "recruiter@example.com",
            received_at: "2026-05-14T12:00:00Z",
            is_read: false,
            labels: [],
            ai_summary: "Reply by Friday.",
            ai_category: "action_required",
            triage_category: "action_required",
            deadline_extracted: "2026-05-16",
            action_items: [],
            ai_processed: true,
            pickup_used: false,
            is_archived: false,
            account_color: "#2563eb",
            account_email: "alex@example.com",
            created_at: "2026-05-14T12:00:00Z",
          },
        ],
        next_cursor: null,
      },
    });
  });

  await page.route("**/pickup-codes**", async (route) => {
    await route.fulfill({
      json: {
        items: [
          {
            email_id: "pickup-1",
            pickup_code: "A1B2C3",
            pickup_expiry: "2026-05-15",
            pickup_used_at: null,
            retailer: "Amazon",
            locker_location: "Union Locker",
            sender_email: "locker@amazon.com",
            subject: "Your pickup code",
            received_at: "2026-05-14T13:00:00Z",
          },
        ],
      },
    });
  });

  await page.route("**/users/me/context", async (route) => {
    context = "Job Hunting";
    await route.fulfill({
      json: {
        user: {
          id: "user-1",
          email: "alex@example.com",
          default_context: context,
          created_at: "2026-05-14T12:00:00Z",
        },
        job_id: "job-1",
        total: 1,
      },
    });
  });

  await page.route("**/jobs/job-1", async (route) => {
    jobPolls += 1;
    await route.fulfill({ json: { status: jobPolls > 1 ? "done" : "running", processed: 1, total: 1 } });
  });

  await page.goto("/");
  await expect(page.getByText("Review today's school application checklist.")).toBeVisible();
  await expect(page.getByText("A1B2C3")).toBeVisible();

  await page.getByRole("button", { name: "Job Hunting" }).click();
  await expect(page.getByText("Re-triaging the last 100 emails...")).toBeVisible();
  await expect(page.getByText("Done - your inbox now reflects Job Hunting")).toBeVisible();
  await expect(page.getByText("Reply to recruiter about interview time.")).toBeVisible();
});
