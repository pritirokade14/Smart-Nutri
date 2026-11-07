import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({ auth: {} }),
}));

afterEach(() => vi.unstubAllEnvs());

describe("getApi", () => {
  it("throws when the API base URL is unset", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "");
    vi.resetModules();
    const { getApi } = await import("@/lib/api/client");
    expect(() => getApi()).toThrow(/NEXT_PUBLIC_API_BASE_URL/);
  });
});

describe("isTargetsPath", () => {
  it("matches targets routes with and without a base URL path", async () => {
    const { isTargetsPath } = await import("@/lib/api/client");
    const base = "http://api.test";
    expect(isTargetsPath(`${base}/v1/targets`, base)).toBe(true);
    expect(isTargetsPath(`${base}/v1/targets/display`, base)).toBe(true);
    expect(isTargetsPath(`${base}/v1/members`, base)).toBe(false);
    const prefixed = "https://host/api/";
    expect(
      isTargetsPath("https://host/api/v1/targets/settings", prefixed),
    ).toBe(true);
    expect(isTargetsPath("https://host/api/v1/meals", prefixed)).toBe(false);
  });
});
