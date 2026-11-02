// @vitest-environment node
import { NextRequest } from "next/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const claims = vi.hoisted(() => ({ value: null as null | { sub: string } }));
vi.mock("@supabase/ssr", () => ({
  createServerClient: () => ({
    auth: {
      getClaims: async () => ({ data: { claims: claims.value }, error: null }),
    },
  }),
}));

import { proxy } from "@/proxy";

const req = (path: string) => new NextRequest(`http://localhost:3000${path}`);

describe("proxy", () => {
  beforeEach(() => {
    claims.value = null;
  });

  it("protected path redirects when signed out", async () => {
    const res = await proxy(req("/en/home"));
    expect(res.status).toBe(302);
    expect(res.headers.get("location")).toMatch(
      /\/en\/sign-in\?next=%2Fen%2Fhome/,
    );
  });

  it("protected path passes when signed in", async () => {
    claims.value = { sub: "u1" };
    const res = await proxy(req("/en/home"));
    expect(res.status).not.toBe(302);
  });

  it("public path never redirects", async () => {
    expect((await proxy(req("/hi"))).status).not.toBe(302);
    expect((await proxy(req("/en/sign-in"))).status).not.toBe(302);
  });

  it("csp present with nonce", async () => {
    const res = await proxy(req("/en"));
    const csp = res.headers.get("content-security-policy") ?? "";
    expect(csp).toMatch(/script-src 'self' 'nonce-[^']+' 'strict-dynamic'/);
    expect(csp).not.toMatch(/script-src[^;]*'unsafe-(inline|eval)'/);
    expect(csp).toContain("frame-ancestors 'none'");
    expect(res.headers.get("x-frame-options")).toBe("DENY");
    expect(res.headers.get("referrer-policy")).toBe(
      "strict-origin-when-cross-origin",
    );
    expect(res.headers.get("permissions-policy")).toBe(
      "camera=(self), microphone=(self)",
    );
  });

  it("nonce differs per request", async () => {
    const a = (await proxy(req("/en"))).headers.get("content-security-policy");
    const b = (await proxy(req("/en"))).headers.get("content-security-policy");
    expect(a).not.toBe(b);
  });

  it("redirects also carry security headers", async () => {
    const res = await proxy(req("/en/home"));
    expect(res.headers.get("x-frame-options")).toBe("DENY");
  });
});
