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

describe("isWeightsPath", () => {
  it("matches weights routes only, with and without a base URL path", async () => {
    const { isWeightsPath } = await import("@/lib/api/client");
    const base = "http://api.test";
    expect(isWeightsPath(`${base}/v1/weights`, base)).toBe(true);
    expect(isWeightsPath(`${base}/v1/weights/trend`, base)).toBe(true);
    expect(isWeightsPath(`${base}/v1/weights/2026-11-07`, base)).toBe(true);
    expect(isWeightsPath(`${base}/v1/weightsx`, base)).toBe(false);
    expect(isWeightsPath(`${base}/v1/meals`, base)).toBe(false);
    expect(
      isWeightsPath("https://host/api/v1/weights", "https://host/api/"),
    ).toBe(true);
  });
});
