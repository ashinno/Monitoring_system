import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  reporter: [
    ["list"],
    ["junit", { outputFile: "reports/playwright-junit.xml" }],
    ["html", { outputFolder: "reports/playwright-html", open: "never" }],
  ],
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: [
    {
      command: "python -m uvicorn main:app --host 127.0.0.1 --port 8000",
      cwd: "backend",
      url: "http://127.0.0.1:8000/docs",
      reuseExistingServer: !process.env.CI,
      env: {
        SENTINEL_DISABLE_BACKGROUND_TASKS: "1",
        SENTINEL_TESTING: "1",
        SENTINEL_DISABLE_CELERY: "1",
        DATABASE_URL: "sqlite:///./sentinel_e2e.db",
        SECRET_KEY: "test-secret-key",
        DEFAULT_ADMIN_ID: "admin",
        DEFAULT_ADMIN_PASSWORD: "admin",
        DEFAULT_ANALYST_ID: "analyst",
        DEFAULT_ANALYST_PASSWORD: "password",
      },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 3000",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
