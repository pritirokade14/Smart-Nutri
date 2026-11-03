import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { consentPurposes } from "@/lib/api/consent-required";
import { apiStub, envelope, json } from "../../support/api-stub";

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: {
      getSession: async () => ({
        data: { session: { access_token: "token" } },
      }),
    },
  }),
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

import { getApi, setConsentRequiredHandler } from "@/lib/api/client";

let api: ReturnType<typeof apiStub>;
beforeEach(() => {
  fetchMock.mockReset();
  api = apiStub(fetchMock);
});
let unregister: (() => void) | undefined;
afterEach(() => unregister?.());

describe("consentPurposes", () => {
  it("reads details.purposes from the route gate's 403", async () => {
    const res = json(
      403,
      envelope("consent_required", { purposes: ["terms", "ai_processing"] }),
    );
    expect(await consentPurposes(res)).toEqual(["terms", "ai_processing"]);
  });

  it("ignores the members gate (singular purpose), unknown purposes and other errors", async () => {
    expect(
      await consentPurposes(
        json(403, envelope("consent_required", { purpose: "health_data" })),
      ),
    ).toBeNull();
    expect(
      await consentPurposes(
        json(403, envelope("consent_required", { purposes: ["marketing"] })),
      ),
    ).toBeNull();
    expect(await consentPurposes(json(403, envelope("forbidden")))).toBeNull();
    expect(
      await consentPurposes(new Response("not json", { status: 403 })),
    ).toBeNull();
  });
});

describe("getApi routes consent_required", () => {
  it("calls the handler with the missing purposes, and the caller still gets the error", async () => {
    api.on(
      "POST",
      "/v1/analyze",
      json(403, envelope("consent_required", { purposes: ["terms"] })),
    );
    const handler = vi.fn();
    unregister = setConsentRequiredHandler(handler);
    const result = await getApi().POST("/v1/analyze", {
      body: { barcode: "8901063201089", language: "en" },
    });
    expect(handler).toHaveBeenCalledWith(["terms"]);
    expect(result.response.status).toBe(403);
    expect(result.error).toMatchObject({ error: { code: "consent_required" } });
  });

  it("does not call the handler for other 403s or for the members gate", async () => {
    api
      .on(
        "POST",
        "/v1/members",
        json(403, envelope("consent_required", { purpose: "health_data" })),
      )
      .on("GET", "/v1/members", json(403, envelope("forbidden")));
    const handler = vi.fn();
    unregister = setConsentRequiredHandler(handler);
    await getApi().POST("/v1/members", {
      body: { name: "Dad", relation: "parent" } as never,
    });
    await getApi().GET("/v1/members");
    expect(handler).not.toHaveBeenCalled();
  });
});
