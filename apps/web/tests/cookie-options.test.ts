// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { supabaseCookieOptions } from "@/lib/supabase/options";

afterEach(() => vi.unstubAllEnvs());

describe("supabaseCookieOptions", () => {
  it("is Secure in production only, always SameSite=Lax", () => {
    vi.stubEnv("NODE_ENV", "production");
    expect(supabaseCookieOptions()).toEqual({ secure: true, sameSite: "lax" });
    vi.stubEnv("NODE_ENV", "development");
    expect(supabaseCookieOptions()).toEqual({ secure: false, sameSite: "lax" });
  });
});
