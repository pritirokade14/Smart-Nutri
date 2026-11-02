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

import { readdirSync } from "node:fs";
import { join } from "node:path";
import { PUBLIC, proxy } from "@/proxy";

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

  it.each(["/en/scan", "/en/result/8901063201089"])(
    "protects %s",
    async (path) => {
      const res = await proxy(req(path));
      expect(res.status).toBe(302);
      expect(res.headers.get("location")).toContain("/en/sign-in");
    },
  );

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

  it.each(["/en/%68ome", "/en/hom%65", "/%65n/home", "/en/%E0%A4%A"])(
    "encoded protected path %s redirects when signed out",
    async (p) => {
      const res = await proxy(req(p));
      expect(res.status).toBe(302);
      expect(res.headers.get("location")).toMatch(/\/en\/sign-in/);
    },
  );

  it.each(["/en/members", "/en/anything-new", "/hi/result/123", "/mr/x/y"])(
    "default-deny: %s redirects when signed out",
    async (path) => {
      const res = await proxy(req(path));
      expect(res.status).toBe(302);
      expect(res.headers.get("location")).toContain("/sign-in?next=");
    },
  );

  it.each([
    "/en",
    "/en/",
    "/en/sign-in",
    "/en/p/8901063201089",
    "/hi/how-we-score",
  ])("public %s does not redirect when signed out", async (path) => {
    expect((await proxy(req(path))).status).not.toBe(302);
  });

  it("every (public) route segment is in PUBLIC", () => {
    const dir = join(process.cwd(), "src/app/[locale]/(public)");
    const segs = readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isDirectory())
      .map((e) => e.name);
    expect(segs.length).toBeGreaterThan(0);
    for (const s of segs) expect(PUBLIC.has(s), s).toBe(true);
  });

  it("redirects also carry security headers", async () => {
    const res = await proxy(req("/en/home"));
    expect(res.headers.get("x-frame-options")).toBe("DENY");
  });
});
