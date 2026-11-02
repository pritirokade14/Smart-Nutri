// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from "vitest";

const exchange = vi.hoisted(() => vi.fn());
vi.mock("@/lib/supabase/server", () => ({
  createSupabaseServerClient: async () => ({
    auth: { exchangeCodeForSession: exchange },
  }),
}));

import { GET } from "@/app/auth/callback/route";

const call = (qs: string) =>
  GET(new Request(`http://localhost:3000/auth/callback?${qs}`));

describe("auth callback", () => {
  beforeEach(() => exchange.mockReset().mockResolvedValue({ error: null }));

  it("redirects to a same-origin next", async () => {
    const res = await call("code=abc&next=/en/scan");
    expect(res.headers.get("location")).toBe("http://localhost:3000/en/scan");
    expect(exchange).toHaveBeenCalledWith("abc");
  });

  it("ignores cross-origin next", async () => {
    for (const bad of ["https://evil.example", "//evil.example", "/%5Cevil"]) {
      const res = await call(`code=abc&next=${encodeURIComponent(bad)}`);
      expect(res.headers.get("location")).toBe("http://localhost:3000/en/home");
    }
  });

  it("goes to sign-in on failure or missing code", async () => {
    exchange.mockResolvedValue({ error: new Error("bad") });
    expect((await call("code=abc")).headers.get("location")).toContain(
      "/en/sign-in?error=callback",
    );
    expect((await call("next=/en/home")).headers.get("location")).toContain(
      "/en/sign-in?error=callback",
    );
  });
});
