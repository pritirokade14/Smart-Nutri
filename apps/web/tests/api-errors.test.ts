import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  type ErrorEnvelope,
  isErrorEnvelope,
  toApiError,
} from "@/lib/api/errors";

const envelope: ErrorEnvelope = {
  error: {
    code: "rate_limited_scans",
    message_key: "error.rate_limited_scans",
    details: { retry_after: 30 },
  },
};

describe("toApiError", () => {
  it("reads the code and details from the API envelope", () => {
    const err = toApiError(envelope, 429);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("rate_limited_scans");
    expect(err.status).toBe(429);
    expect(err.details).toEqual({ retry_after: 30 });
  });

  it.each([
    undefined,
    null,
    "Internal Server Error",
    { detail: [{ loc: ["query", "n"] }] },
    { error: "nope" },
    { error: { code: 5, message_key: "error.x" } },
  ])("falls back to internal_error for %j", (body) => {
    expect(toApiError(body, 500).code).toBe("internal_error");
  });

  it("recognises only the envelope shape", () => {
    expect(isErrorEnvelope(envelope)).toBe(true);
    expect(isErrorEnvelope({ error: { code: "x" } })).toBe(false);
  });
});

describe("fetchMe", () => {
  afterEach(() => {
    vi.resetModules();
    vi.doUnmock("@/lib/api/client");
  });

  async function withGet(get: () => Promise<unknown>) {
    vi.doMock("@/lib/api/client", () => ({ getApi: () => ({ GET: get }) }));
    return (await import("@/features/me/api/me")).fetchMe;
  }

  it("throws the envelope code", async () => {
    const fetchMe = await withGet(async () => ({
      error: {
        error: {
          code: "auth_invalid",
          message_key: "error.auth_invalid",
          details: {},
        },
      },
      response: { status: 401 },
    }));
    await expect(fetchMe()).rejects.toMatchObject({
      code: "auth_invalid",
      status: 401,
    });
  });

  it("maps a fetch failure to network", async () => {
    const fetchMe = await withGet(async () => {
      throw new TypeError("Failed to fetch");
    });
    await expect(fetchMe()).rejects.toMatchObject({ code: "network" });
  });

  it("returns data on success", async () => {
    const me = { id: "u", email: null, display_name: null, language: "en" };
    const fetchMe = await withGet(async () => ({
      data: me,
      response: { status: 200 },
    }));
    await expect(fetchMe()).resolves.toEqual(me);
  });
});
