import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const apiURL = (process.env.API_URL ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

/**
 * Playwright E2E — local / manual only (not the default Frontend CI PR gate).
 *
 * WHY: webServer boots FastAPI (`uv run uvicorn`) and needs Postgres + backend
 * env (SECRET_KEY, DATABASE_URL, Stripe test keys for checkout flows). A
 * Node-only GitHub job cannot honestly run these tests.
 *
 * Run locally:
 *   make e2e-critical
 *
 * Or manually (two terminals):
 *   cd backend && uv run uvicorn app.main:app --port 8000
 *   cd frontend && npm run dev
 *   cd frontend && npm run test:e2e:critical
 *
 * Override URL: PLAYWRIGHT_BASE_URL=http://localhost:3000 npm run test:e2e
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "cd ../backend && uv run uvicorn app.main:app --port 8000",
      url: `${apiURL}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        ...process.env,
        FRONTEND_URL: baseURL,
      },
    },
    {
      command: "npm run dev",
      url: baseURL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
