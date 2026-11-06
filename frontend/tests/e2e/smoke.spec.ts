import { expect, test } from "@playwright/test";

test("landing page renders the application shell", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      name: /public issues, tracked to resolution/i,
    }),
  ).toBeVisible();
  await expect(page.getByText("Phase 3 skeleton")).toBeVisible();
});
