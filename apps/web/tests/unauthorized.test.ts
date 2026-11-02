import { QueryClient } from "@tanstack/react-query";
import { afterEach, describe, expect, it, vi } from "vitest";
import { clearAnalyzeCache } from "@/features/analysis/api/useAnalyzeBarcode";

const getSession = vi.hoisted(() => vi.fn());
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({ auth: { getSession } }),
}));

import { getApi, setUnauthorizedHandler } from "@/lib/api/client";
import { handleUnauthorized } from "@/lib/api/unauthorized";

// openapi-fetch captures global fetch when the (cached) client is created, so
// stub once with a delegating fetch whose behaviour each test sets.
let respond: () => Promise<Response> = async () => new Response("{}");
vi.stubGlobal("fetch", () => respond());
vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "http://api.test");

function run(token: string | null, status: number | "network") {
  getSession.mockResolvedValue({
    data: { session: token ? { access_token: token } : null },
  });
  respond = async () => {
    if (status === "network") throw new TypeError("offline");
    return new Response("{}", {
      status,
      headers: { "content-type": "application/json" },
    });
  };
  const signOut = vi.fn(async () => undefined);
  const navigate = vi.fn();
  setUnauthorizedHandler(() =>
    handleUnauthorized({
      locale: "hi",
      signOut,
      currentPath: () => "/hi/members?x=1",
      navigate,
    }),
  );
  return { signOut, navigate };
}

afterEach(() => {
  setUnauthorizedHandler(undefined);
});

describe("sign-out clears cached verdicts", () => {
  it("clearAnalyzeCache removes only ['analyze'] queries", () => {
    const client = new QueryClient();
    client.setQueryData(["analyze", "8901", "en"], { x: 1 });
    client.setQueryData(["other"], { y: 2 });
    clearAnalyzeCache(client);
    expect(client.getQueryData(["analyze", "8901", "en"])).toBeUndefined();
    expect(client.getQueryData(["other"])).toEqual({ y: 2 });
  });
  it("handleUnauthorized clears the cache before navigating", async () => {
    const order: string[] = [];
    await handleUnauthorized({
      locale: "en",
      clearCache: () => order.push("clear"),
      signOut: async () => order.push("signOut"),
      currentPath: () => "/en/scan",
      navigate: () => order.push("navigate"),
    });
    expect(order).toEqual(["clear", "signOut", "navigate"]);
  });
});

describe("401 policy", () => {
  it("401 with token signs out and redirects", async () => {
    const { signOut, navigate } = run("tok", 401);
    await getApi().GET("/v1/me" as never);
    expect(signOut).toHaveBeenCalledOnce();
    expect(navigate).toHaveBeenCalledWith(
      "/hi/sign-in?next=%2Fhi%2Fmembers%3Fx%3D1",
    );
  });
  it("401 without token does nothing", async () => {
    const { signOut, navigate } = run(null, 401);
    await getApi().GET("/v1/me" as never);
    expect(signOut).not.toHaveBeenCalled();
    expect(navigate).not.toHaveBeenCalled();
  });
  it("503 does nothing", async () => {
    const { signOut } = run("tok", 503);
    await getApi().GET("/v1/me" as never);
    expect(signOut).not.toHaveBeenCalled();
  });
  it("network error does nothing", async () => {
    const { signOut } = run("tok", "network");
    await getApi()
      .GET("/v1/me" as never)
      .catch(() => undefined);
    expect(signOut).not.toHaveBeenCalled();
  });
});
