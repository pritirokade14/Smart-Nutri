// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from "vitest";

const claims = vi.hoisted(() => ({ value: null as null | { sub: string } }));
vi.mock("@/lib/supabase/server", () => ({
  createSupabaseServerClient: async () => ({
    auth: {
      getClaims: async () => ({ data: { claims: claims.value }, error: null }),
    },
  }),
}));
vi.mock("next/navigation", () => ({
  redirect: (to: string) => {
    throw new Error(`REDIRECT:${to}`);
  },
}));
vi.mock("@/app/providers", () => ({ Providers: () => null }));

import AppLayout from "@/app/[locale]/(app)/layout";

const props = { children: null, params: Promise.resolve({ locale: "en" }) };

describe("(app) layout", () => {
  beforeEach(() => {
    claims.value = null;
  });
  it("redirects to sign-in without a session", async () => {
    await expect(AppLayout(props)).rejects.toThrow(/REDIRECT:\/en\/sign-in/);
  });
  it("renders with a session", async () => {
    claims.value = { sub: "u" };
    await expect(AppLayout(props)).resolves.toBeTruthy();
  });
});
