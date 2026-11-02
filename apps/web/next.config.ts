import { withSentryConfig } from "@sentry/nextjs/config";
import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["@smartnutri/api-client"],
};

// Source-map upload runs only when SENTRY_AUTH_TOKEN is set (CI); no tunnel route, no telemetry.
export default withSentryConfig(withNextIntl(nextConfig), {
  silent: true,
  telemetry: false,
  authToken: process.env.SENTRY_AUTH_TOKEN,
});
