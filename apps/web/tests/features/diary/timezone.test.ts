import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiStub, json } from "../../support/api-stub";

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: { getSession: async () => ({ data: { session: null } }) },
  }),
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

import { resetTimezoneSync, syncTimezone } from "@/lib/timezone";

const me = (timezone: string) => ({
  id: "5f0c3a52-6f1e-4c9b-9d1a-2b7e8c4d1a01",
  email: null,
  display_name: null,
  language: "en" as const,
  created_at: "2026-01-01T00:00:00Z",
  timezone,
});
const browserZone = () => Intl.DateTimeFormat().resolvedOptions().timeZone;

beforeEach(() => {
  fetchMock.mockReset();
  resetTimezoneSync();
});

describe("syncTimezone", () => {
  it("sends the zone only when it differs", async () => {
    const api = apiStub(fetchMock).on("PUT", "/v1/me/timezone", (_c) =>
      json(200, me(browserZone())),
    );
    await syncTimezone(me(browserZone()));
    expect(api.callsTo("PUT", "/v1/me/timezone")).toHaveLength(0);

    resetTimezoneSync();
    await syncTimezone(me("Pacific/Kiritimati-not-the-browser"));
    const sent = api.callsTo("PUT", "/v1/me/timezone");
    expect(sent).toHaveLength(1);
    expect(sent[0].body).toEqual({ timezone: browserZone() });
  });

  it("sends at most once per session", async () => {
    const api = apiStub(fetchMock).on(
      "PUT",
      "/v1/me/timezone",
      json(200, me("x")),
    );
    await syncTimezone(me("Somewhere/Else"));
    await syncTimezone(me("Somewhere/Else"));
    expect(api.callsTo("PUT", "/v1/me/timezone")).toHaveLength(1);
  });

  it("a failing request is ignored", async () => {
    fetchMock.mockRejectedValue(new TypeError("offline"));
    await expect(syncTimezone(me("Somewhere/Else"))).resolves.toBeUndefined();
  });

  it("an unreadable browser zone sends nothing", async () => {
    const api = apiStub(fetchMock).on(
      "PUT",
      "/v1/me/timezone",
      json(200, me("x")),
    );
    const spy = vi.spyOn(Intl, "DateTimeFormat").mockImplementation((() => {
      throw new Error("no zone");
    }) as never);
    await syncTimezone(me("Somewhere/Else"));
    spy.mockRestore();
    expect(api.callsTo("PUT", "/v1/me/timezone")).toHaveLength(0);
  });
});
