import { test, expect } from "@playwright/test";

test.use({ storageState: "frontend/tests/e2e/storage-state.json" });

test("unified inbox happy path", async ({ page }) => {
  await page.goto("/inbox");
  await expect(page.getByTestId("email-card").first()).toBeVisible();

  await page.getByTestId("email-card").first().click();
  await expect(page.getByRole("dialog")).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();

  await page.keyboard.press("e");
  await expect(page.getByTestId("email-card").first()).toBeVisible();

  await page.getByRole("tab", { name: /Action Required/i }).click();
  await expect(page).toHaveURL(/tab=action_required/);
});
