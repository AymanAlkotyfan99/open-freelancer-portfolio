import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  workers: 1,
  fullyParallel: false,
  use: { baseURL: "http://127.0.0.1:3000", trace: "retain-on-failure" },
  webServer: [
    {
      command: "uv run python tests/e2e_seed.py && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000",
      cwd: "../api",
      url: "http://127.0.0.1:8000/api/v1/health",
      env: {
        DATABASE_URL: "sqlite+aiosqlite:///./e2e.db",
        FRONTEND_URL: "http://127.0.0.1:3000",
        CORS_ORIGINS: "http://127.0.0.1:3000",
        JWT_SECRET_KEY: "e2e-only-jwt-secret-key-with-32-chars",
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: "npm.cmd run dev -- --hostname 127.0.0.1",
      url: "http://127.0.0.1:3000/en",
      env: {
        NEXT_PUBLIC_API_URL: "http://127.0.0.1:8000/api/v1",
        NEXT_PUBLIC_SITE_URL: "http://127.0.0.1:3000",
        CONTENT_REVALIDATE_SECONDS: "0",
      },
      reuseExistingServer: false,
      timeout: 180_000,
    },
  ],
});
