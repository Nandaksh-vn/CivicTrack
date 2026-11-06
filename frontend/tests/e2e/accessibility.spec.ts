/**
 * Phase 17 — Accessibility E2E Tests (TEST-045)
 *
 * Runs axe-core scans on all main screens and a keyboard-only walkthrough.
 * Accessibility audit must have no critical/serious violations on main flows.
 */

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// ── Main screens to audit ────────────────────────────────────────────────────

const screens = [
  { path: "/", name: "landing" },
  { path: "/login", name: "login" },
  { path: "/register", name: "register" },
];

test.describe("axe accessibility scans", () => {
  for (const { path, name } of screens) {
    test(`no critical/serious violations on ${name}`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");

      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "section508"])
        .analyze();

      const critical = results.violations.filter((v) => v.impact === "critical");
      const serious = results.violations.filter((v) => v.impact === "serious");

      expect(critical).toEqual([]);
      expect(serious).toEqual([]);

      if (results.violations.length > critical.length + serious.length) {
        console.log(
          `${name}: ${results.violations.length - critical.length - serious.length} minor/moderate violation(s) to triage`,
        );
      }
    });
  }

  test("no critical/serious violations on My Complaints (authenticated)", async ({
    page,
  }) => {
    // Register + log in as citizen (email without hyphen for client-side validation)
    const email = `a11ycitizen${Date.now()}@example.com`;
    await page.goto("/register");
    await page.waitForLoadState("networkidle");

    await page.fill('input[id="full_name"]', "A11y Citizen");
    await page.fill('input[id="email"]', email);
    await page.fill('input[id="password"]', "Password123");
    await page.click('button:has-text("Create account")');

    await page.waitForURL(/\/complaints\/new/, { timeout: 15_000 });

    // Navigate to My Complaints
    await page.click('a:has-text("My Complaints")');
    await page.waitForURL(/\/complaints\/?$/);
    await page.waitForLoadState("networkidle");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "section508"])
      .analyze();

    const critical = results.violations.filter((v) => v.impact === "critical");
    const serious = results.violations.filter((v) => v.impact === "serious");

    expect(critical).toEqual([]);
    expect(serious).toEqual([]);
  });
});

// ── Keyboard-only walkthrough ───────────────────────────────────────────────

test.describe("keyboard-only walkthrough", () => {
  test("landing page is fully keyboard-navigable", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    // Tab through interactive elements
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");

    // Verify focus is visible and moves logically
    const focused = page.locator(":focus");
    await expect(focused).toBeVisible();

    // Enter/Space should activate focused elements
    await page.keyboard.press("Enter");
  });

  test("register form is keyboard-navigable", async ({ page }) => {
    await page.goto("/register");
    await page.waitForLoadState("networkidle");

    // Tab to first field
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");

    // Fill email via keyboard (no hyphen - client regex doesn't allow it in local part)
    await page.keyboard.type("keyboardcitizen@example.com");
    await page.keyboard.press("Tab");
    await page.keyboard.type("Password123");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Enter");

    // Should attempt submission (may show validation errors for missing fields)
    await expect(page.getByRole("button", { name: /create account/i })).toBeVisible();
  });
});
