import { expect, test } from "@playwright/test";

test.use({ storageState: "tests/e2e/storage-state.json" });

type ContactTag = {
  id: string;
  identifier: string;
  tag: "professor" | "friend" | "recruiter" | "custom";
  custom_label: string | null;
  color: string;
  created_at: string;
};

function grouped(tags: ContactTag[]) {
  return {
    professor: tags.filter((tag) => tag.tag === "professor"),
    friend: tags.filter((tag) => tag.tag === "friend"),
    recruiter: tags.filter((tag) => tag.tag === "recruiter"),
    custom: tags.filter((tag) => tag.tag === "custom"),
  };
}

test("contact tags persist after refresh and domain tags highlight inbox emails", async ({ page }) => {
  let tags: ContactTag[] = [];

  await page.route(/.*\/contacts$/, async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ json: grouped(tags) });
      return;
    }

    if (route.request().method() === "POST") {
      const body = JSON.parse(route.request().postData() ?? "{}");
      const created: ContactTag = {
        id: "tag-uw-domain",
        identifier: body.identifier,
        tag: body.tag,
        custom_label: body.custom_label ?? null,
        color: body.color ?? "#3B82F6",
        created_at: "2026-05-14T12:00:00Z",
      };
      tags = [created, ...tags];
      await route.fulfill({ json: { tag: created, retroactive_count: 1, job_id: null } });
      return;
    }

    await route.fallback();
  });

  await page.route(/.*\/emails\/counts$/, async (route) => {
    await route.fulfill({
      json: { all: 1, action_required: 1, worth_reading: 0, auto_archive: 0 },
    });
  });

  await page.route(/.*\/emails.*/, async (route) => {
    const contactTag = tags.some((tag) => tag.identifier === "@uw.edu")
      ? { label: "Professor", color: "#3B82F6" }
      : null;
    await route.fulfill({
      json: {
        items: [
          {
            id: "email-uw-1",
            user_id: "user-1",
            account_id: "account-1",
            gmail_id: "gmail-1",
            thread_id: null,
            subject: "Office hours reminder",
            sender: "dean@uw.edu",
            received_at: "2026-05-14T12:00:00Z",
            is_read: false,
            labels: [],
            ai_summary: "Professor shared office-hours details.",
            ai_category: "action_required",
            triage_category: "action_required",
            deadline_extracted: null,
            action_items: [],
            ai_processed: true,
            pickup_used: false,
            is_archived: false,
            contact_tag: contactTag,
            account_color: "#2563eb",
            account_email: "alex@example.com",
            created_at: "2026-05-14T12:00:00Z",
          },
        ],
        next_cursor: null,
      },
    });
  });

  await page.goto("/contacts");
  await expect(page.getByText("No tagged contacts yet")).toBeVisible();

  await page.getByRole("button", { name: "Add tag" }).click();
  await page.getByLabel("Email or domain").fill("@uw.edu");
  await page.getByLabel("Tag type").click();
  await page.getByRole("option", { name: "Professor" }).click();
  await page.getByRole("button", { name: "Add tag" }).click();

  await expect(page.getByText("@uw.edu")).toBeVisible();

  await page.reload();
  await expect(page.getByText("@uw.edu")).toBeVisible();

  await page.goto("/inbox");
  await expect(page.getByText("dean@uw.edu")).toBeVisible();
  await expect(page.getByText("Professor")).toBeVisible();
});
