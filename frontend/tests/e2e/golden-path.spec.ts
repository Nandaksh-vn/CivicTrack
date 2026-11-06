/**
 * Phase 17 — E2E Golden Path & Negative Tests (TEST-042, TEST-043, TEST-044)
 *
 * Exercises CivicTrack against a running backend and frontend.
 * Requires:
 *   - Backend at http://127.0.0.1:8000 (already running via Docker)
 *   - Frontend dev server on port 5173 (started by Playwright webServer)
 *   - Vite proxy /api -> http://localhost:8000
 *
 * Tests that require complex frontend-backend wiring (complaint creation,
 * escalation trigger) are skipped until the corresponding endpoints are
 * wired to the frontend (INT-010, Phase 15-16).
 */

import { expect, test, type Page } from "@playwright/test";

// ── Helpers ──────────────────────────────────────────────────────────────────

async function registerCitizen(page: Page, email: string, password = "Password123") {
  await page.goto("/register");
  await page.waitForLoadState("networkidle");

  await page.fill('input[id="full_name"]', "E2E Citizen");
  await page.fill('input[id="email"]', email);
  await page.fill('input[id="password"]', password);
  await page.click('button:has-text("Create account")');

  // Wait up to 15s for either navigation to complaints/new or an error
  await page.waitForURL(/\/complaints\/new/, { timeout: 15_000 }).catch(() => {
    // If navigation didn't happen, check for error message
    const error = page.locator('p[role="alert"]');
    if (await error.isVisible()) {
      throw new Error(`Registration failed: ${await error.textContent()}`);
    }
  });
}

async function login(page: Page, email: string, password = "Password123") {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  await page.fill('input[id="email"]', email);
  await page.fill('input[id="password"]', password);
  await page.click('button:has-text("Log in")');

  await page.waitForURL(/\/complaints/, { timeout: 15_000 }).catch(() => {
    const error = page.locator('p[role="alert"]');
    if (await error.isVisible()) {
      throw new Error(`Login failed: ${await error.textContent()}`);
    }
  });
}

// ── TEST-042: Golden path — auth + navigation ────────────────────────────────

test("citizen can register and reach the complaint submission page", async ({
  page,
}) => {
  const email = `citizen-${Date.now()}@example.com`;
  await registerCitizen(page, email);

  // After registration, the app navigates to /complaints/new
  await expect(
    page.getByRole("heading", { name: /report a problem/i }),
  ).toBeVisible();
});

test("registered citizen can log in and reach My Complaints", async ({
  page,
}) => {
  const email = `citizen-${Date.now()}@example.com`;
  await registerCitizen(page, email);

  // Log out then log back in
  await page.goto("/login");
  await login(page, email);

  await expect(page.getByRole("heading", { name: /my complaints/i })).toBeVisible();
});

// ── TEST-043: Negative E2E — citizen blocked from staff routes ─────────────

test("citizen is blocked from superintendent escalations page", async ({
  page,
}) => {
  const email = `citizen-${Date.now()}@example.com`;
  await registerCitizen(page, email);

  await page.goto("/superintendent/escalations");
  await page.waitForLoadState("networkidle");
  await expect(page.getByText(/you do not have access to this page/i)).toBeVisible();
});

test("citizen is blocked from admin users page", async ({ page }) => {
  const email = `citizen-${Date.now()}@example.com`;
  await registerCitizen(page, email);

  await page.goto("/admin/users");
  await page.waitForLoadState("networkidle");
  await expect(page.getByText(/you do not have access to this page/i)).toBeVisible();
});

test("anonymous user is redirected to login from protected routes", async ({
  page,
}) => {
  await page.goto("/complaints");
  await page.waitForLoadState("networkidle");
  await expect(page.getByRole("heading", { name: /log in to civictrack/i })).toBeVisible();
});

// ── TEST-044: Idempotency — repeated escalation trigger ────────────────────
// Skipped until escalation worker + internal endpoint wired to frontend (INT-010).
test.skip("repeated escalation trigger yields one escalation record", async ({
  page: _page,
}) => {
  test.skip(true, "escalation worker + internal endpoint not yet wired to frontend");
});
