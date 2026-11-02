// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const exchange = vi.hoisted(() => vi.fn());
vi.mock("@/lib/supabase/server", () => ({
  createSupabaseServerClient: async () => ({
    auth: { exchangeCodeForSession: exchange },
  }),
}));

import { GET } from "@/app/auth/callback/route";

// The container binds 0.0.0.0:8080, so request.url must never be the redirect base.
const call = (qs: string, headers?: Record<string, string>) =>
  GET(new Request(`http://0.0.0.0:8080/auth/callback?${qs}`, { headers }));

describe("auth callback", () => {
  beforeEach(() => {
    exchange.mockReset().mockResolvedValue({ error: null });
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "http://localhost:3000");
  });
  afterEach(() => vi.unstubAllEnvs());

  it("redirects to a same-origin next on the site URL", async () => {
    const res = await call("code=abc&next=/en/scan");
    expect(res.headers.get("location")).toBe("http://localhost:3000/en/scan");
    expect(exchange).toHaveBeenCalledWith("abc");
  });

  it("falls back to the request origin only when SITE_URL is unset", async () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "");
    expect((await call("code=a")).headers.get("location")).toBe(
      "http://0.0.0.0:8080/en/home",
    );
  });

  it("ignores cross-origin next", async () => {
    for (const bad of ["https://evil.example", "//evil.example", "/%5Cevil"]) {
      const res = await call(`code=abc&next=${encodeURIComponent(bad)}`);
      expect(res.headers.get("location")).toBe("http://localhost:3000/en/home");
    }
  });

  it("goes to sign-in on failure or missing code", async () => {
    exchange.mockResolvedValue({ error: new Error("bad") });
    expect((await call("code=abc")).headers.get("location")).toBe(
      "http://localhost:3000/en/sign-in?error=callback",
    );
    expect((await call("next=/en/home")).headers.get("location")).toBe(
      "http://localhost:3000/en/sign-in?error=callback",
    );
  });

  it("derives the locale from next or the NEXT_LOCALE cookie", async () => {
    exchange.mockResolvedValue({ error: new Error("bad") });
    expect((await call("code=a&next=/hi/scan")).headers.get("location")).toBe(
      "http://localhost:3000/hi/sign-in?error=callback",
    );
    const res = await call("code=a", { cookie: "NEXT_LOCALE=mr" });
    expect(res.headers.get("location")).toBe(
      "http://localhost:3000/mr/sign-in?error=callback",
    );
  });
});
