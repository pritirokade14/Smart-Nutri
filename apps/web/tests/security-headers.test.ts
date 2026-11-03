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

  it("sends HSTS in production only", () => {
    vi.stubEnv("NODE_ENV", "production");
    expect(securityHeaders("n")["Strict-Transport-Security"]).toBe(
      "max-age=63072000; includeSubDomains",
    );
    vi.stubEnv("NODE_ENV", "development");
    expect(securityHeaders("n")["Strict-Transport-Security"]).toBeUndefined();
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

  it("lets voice answers play from Supabase Storage only (media-src)", () => {
    const csp = securityHeaders("n")["Content-Security-Policy"];
    expect(csp).toContain("media-src 'self' blob: http://127.0.0.1:54321");
    expect(securityHeaders("n")["Permissions-Policy"]).toContain(
      "microphone=(self)",
    );
  });
});
