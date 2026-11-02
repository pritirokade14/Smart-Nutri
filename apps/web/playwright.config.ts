import { defineConfig } from "@playwright/test";

const port = Number(process.env.PORT ?? 3000);
const baseURL = `http://localhost:${port}`;

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL },
  webServer: {
    command: "pnpm start",
    url: `${baseURL}/en`,
    env: { PORT: String(port) },
    reuseExistingServer: false,
    timeout: 120_000,
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
