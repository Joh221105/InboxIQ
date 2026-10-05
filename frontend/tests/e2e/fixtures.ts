import type { Page } from "@playwright/test";

/** Backend origin the app is built against in e2e runs (NEXT_PUBLIC_API_URL). */
export const API_URL = "http://127.0.0.1:8000";

/** Route pattern for one API path, so it can never match an app page like /contacts. */
export function api(path: string): RegExp {
  const escaped = `${API_URL}${path}`.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&");
  return new RegExp(`^${escaped}(\\?.*)?$`);
}

export const connectedAccount = {
  id: "account-1",
  email_address: "alex@example.com",
  provider: "gmail",
  color: "#2563eb",
  last_synced: "2026-05-14T12:00:00Z",
  disconnected_at: null,
};

/** Pages that need an account (inbox, dashboard) render an empty state without one. */
export async function mockConnectedAccount(page: Page): Promise<void> {
  await page.route(api("/accounts"), (route) => route.fulfill({ json: [connectedAccount] }));
}
