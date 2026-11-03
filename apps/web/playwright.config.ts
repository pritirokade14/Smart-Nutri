import { defineConfig } from "@playwright/test";

const port = Number(process.env.PORT ?? 3000);
const stubPort = Number(process.env.STUB_API_PORT ?? 18000);
const stubURL = `http://127.0.0.1:${stubPort}`;
const baseURL = `http://localhost:${port}`;

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL },
  webServer: [
    {
      command: "node e2e/stub-api.mjs",
      url: `${stubURL}/health`,
      env: { STUB_API_PORT: String(stubPort) },
      ignoreHTTPSErrors: true,
      reuseExistingServer: false,
    },
    {
      command: "pnpm start",
      url: `${baseURL}/en`,
      env: {
        PORT: String(port),
        // Dummy public values (NEXT_PUBLIC_* is shipped to browsers anyway).
        NEXT_PUBLIC_SUPABASE_URL: "http://127.0.0.1:54321",
        NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: "dummy-publishable-key",
        NEXT_PUBLIC_API_BASE_URL: stubURL,
        NEXT_PUBLIC_SITE_URL: baseURL,
        NEXT_PUBLIC_FEATURE_PHONE_OTP: "false",
        NEXT_PUBLIC_FEATURE_EMAIL_OTP: "true",
      },
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
