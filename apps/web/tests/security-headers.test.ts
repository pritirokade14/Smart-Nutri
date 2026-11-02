// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { securityHeaders } from "@/lib/security-headers";

afterEach(() => vi.unstubAllEnvs());

describe("securityHeaders", () => {
  it("allows unsafe-eval only in development", () => {
    vi.stubEnv("NODE_ENV", "production");
    expect(securityHeaders("n")["Content-Security-Policy"]).not.toContain(
      "unsafe-eval",
    );
    vi.stubEnv("NODE_ENV", "development");
    expect(securityHeaders("n")["Content-Security-Policy"]).toContain(
      "'unsafe-eval'",
    );
  });

  it("limits connect-src to API, Supabase, Sentry and PostHog", () => {
    const csp = securityHeaders("n")["Content-Security-Policy"];
    expect(csp).toContain("http://127.0.0.1:8000");
    expect(csp).toContain("http://127.0.0.1:54321");
    expect(csp).toContain("https://*.sentry.io");
    expect(csp).toContain("https://*.posthog.com");
    expect(csp).toContain(
      "img-src 'self' data: blob: https://images.openfoodfacts.org",
    );
  });
});
