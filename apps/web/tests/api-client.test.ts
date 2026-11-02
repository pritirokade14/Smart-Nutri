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
