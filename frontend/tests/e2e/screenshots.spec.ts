/**
 * Regenerates the README screenshots in docs/images from mocked API data.
 * Run with `npm run screenshots`; excluded from the normal e2e run.
 */
import { expect, test, type Page } from "@playwright/test";

import { api, connectedAccount } from "./fixtures";

const OUT = "../docs/images";

test.use({ viewport: { width: 1440, height: 900 }, colorScheme: "light" });

function daysFromNow(days: number): string {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

function hoursAgo(hours: number): string {
  return new Date(Date.now() - hours * 3_600_000).toISOString();
}

type Category = "action_required" | "worth_reading" | "auto_archive";

function email(
  id: string,
  category: Category,
  sender: string,
  senderName: string,
  subject: string,
  summary: string,
  hours: number,
  extra: Record<string, unknown> = {},
) {
  return {
    id,
    user_id: "user-1",
    account_id: connectedAccount.id,
    gmail_id: `gmail-${id}`,
    thread_id: null,
    subject,
    sender,
    sender_name: senderName,
    received_at: hoursAgo(hours),
    is_read: hours > 20,
    labels: ["INBOX"],
    ai_summary: summary,
    ai_category: category,
    triage_category: category,
    deadline_extracted: null,
    action_items: [],
    ai_processed: true,
    pickup_used: false,
    is_archived: false,
    account_color: connectedAccount.color,
    account_email: connectedAccount.email_address,
    contact_tag: null,
    created_at: hoursAgo(hours),
    ...extra,
  };
}

const EMAILS = [
  email("e1", "action_required", "recruiting@northwind.example", "Northwind Recruiting", "Final round interview — pick a time", "Schedule your 4-hour final round by Friday; three slots offered.", 1, {
    deadline_extracted: daysFromNow(3),
    contact_tag: { label: "Recruiter", color: "#FDE68A" },
  }),
  email("e2", "action_required", "registrar@state-university.example", "Office of the Registrar", "Transcript upload required", "Upload your official transcript to complete the application.", 3, {
    deadline_extracted: daysFromNow(5),
  }),
  email("e3", "action_required", "no-reply@lockers.example", "Parcel Lockers", "Your package is ready for pickup", "Package waiting at Pine St locker — use code 748291.", 5),
  email("e4", "worth_reading", "prof.chen@state-university.example", "Prof. Chen", "Notes from today's office hours", "Prof. Chen shared slides and a reading list from office hours.", 8, {
    contact_tag: { label: "Professor", color: "#BFDBFE" },
  }),
  email("e5", "worth_reading", "orders@shop.example", "Shop Orders", "Your order has shipped", "Order #48213 shipped; arrives Thursday.", 12),
  email("e6", "worth_reading", "sam@friends.example", "Sam Rivera", "Weekend hike?", "Sam is planning a Saturday hike and asks if you can join.", 20, {
    contact_tag: { label: "Friend", color: "#A7F3D0" },
  }),
  email("e7", "auto_archive", "deals@shop.example", "Shop Deals", "48-hour flash sale", "Promotional sale on home goods.", 26),
  email("e8", "auto_archive", "digest@jobs-board.example", "Jobs Board", "12 new roles match your search", "Weekly job-board digest.", 30),
];

const PICKUP_CODES = [
  {
    email_id: "e3",
    pickup_code: "748291",
    pickup_expiry: daysFromNow(2),
    pickup_used_at: null,
    retailer: "Amazon",
    locker_location: "Pine St Locker",
    sender_email: "no-reply@lockers.example",
    subject: "Your package is ready for pickup",
    received_at: hoursAgo(5),
  },
  {
    email_id: "e9",
    pickup_code: "FX-39201",
    pickup_expiry: daysFromNow(5),
    pickup_used_at: null,
    retailer: "FedEx",
    locker_location: "FedEx Office, 456 University Ave",
    sender_email: "tracking@fedex.example",
    subject: "Package held for pickup",
    received_at: hoursAgo(28),
  },
];

async function mockApi(page: Page): Promise<void> {
  await page.route(api("/accounts"), (route) => route.fulfill({ json: [connectedAccount] }));
  await page.route(api("/users/me"), (route) =>
    route.fulfill({
      json: {
        id: "user-1",
        email: connectedAccount.email_address,
        default_context: "Job Hunting",
        notification_tag_preferences: {},
        data_retention_days: null,
        created_at: hoursAgo(24 * 30),
      },
    }),
  );
  await page.route(api("/digest/today"), (route) =>
    route.fulfill({
      json: {
        generated_at: hoursAgo(0.2),
        context: "Job Hunting",
        degraded: false,
        items: [
          { summary: "Pick a final-round interview slot with Northwind", source_email_id: "e1", sender: "recruiting@northwind.example", deadline: daysFromNow(3) },
          { summary: "Upload your transcript to the registrar", source_email_id: "e2", sender: "registrar@state-university.example", deadline: daysFromNow(5) },
          { summary: "Collect your package from the Pine St locker", source_email_id: "e3", sender: "no-reply@lockers.example", deadline: daysFromNow(2) },
        ],
      },
    }),
  );
  await page.route(api("/emails/counts"), (route) =>
    route.fulfill({ json: { all: 8, action_required: 3, worth_reading: 3, auto_archive: 2 } }),
  );
  await page.route(api("/emails"), (route) => {
    const url = new URL(route.request().url());
    const items = url.searchParams.get("has_deadline")
      ? EMAILS.filter((e) => e.deadline_extracted)
      : EMAILS;
    return route.fulfill({ json: { items, next_cursor: null } });
  });
  await page.route(api("/pickup-codes"), (route) => {
    const used = new URL(route.request().url()).searchParams.get("used") === "true";
    return route.fulfill({ json: { items: used ? [] : PICKUP_CODES } });
  });
}

test("dashboard", async ({ page }) => {
  await mockApi(page);
  await page.goto("/");
  await expect(page.getByText("Here's your briefing")).toBeVisible();
  await page.waitForTimeout(1000); // let the mascot video render a frame
  await page.screenshot({ path: `${OUT}/dashboard.png` });
});

test("inbox", async ({ page }) => {
  await mockApi(page);
  await page.goto("/inbox");
  await expect(page.getByTestId("email-card").first()).toBeVisible();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUT}/inbox.png` });
});

test("pickup codes", async ({ page }) => {
  await mockApi(page);
  await page.goto("/packages");
  await expect(page.getByTestId("pickup-code-card").first()).toBeVisible();
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUT}/packages.png` });
});
