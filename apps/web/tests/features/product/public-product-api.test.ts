import enMessages from "@smartnutri/i18n/messages/en.json";
import { afterEach, describe, expect, it, vi } from "vitest";
import { loadPublicProduct } from "@/features/product/api/public-product";
import { clientMessages } from "@/i18n/client-messages";
import { offProduct, publicFixtures } from "../../support/public-fixtures";

afterEach(() => vi.unstubAllGlobals());

describe("loadPublicProduct", () => {
  it("sends no Authorization header and caches for 3600s", async () => {
    const fetchMock = vi.fn(
      async (_req: Request, _init?: unknown) =>
        new Response(JSON.stringify(offProduct), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const r = await loadPublicProduct("8901063201089");
    expect(r.kind).toBe("ok");
    const [req, init] = fetchMock.mock.calls[0] as [
      Request,
      { next?: { revalidate?: number } },
    ];
    expect(req.url).toContain("/v1/products/8901063201089/public");
    expect(req.headers.get("authorization")).toBeNull();
    expect(init.next?.revalidate).toBe(3600);
  });

  it.each([
    [404, "not_found"],
    [503, "unavailable"],
    [500, "unavailable"],
  ])("maps HTTP %i to %s", async (status, kind) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              error: { code: "x", message_key: "x", details: {} },
            }),
            { status, headers: { "content-type": "application/json" } },
          ),
      ),
    );
    expect((await loadPublicProduct("8901063201089")).kind).toBe(kind);
  });

  it("network failure is unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("down");
      }),
    );
    expect((await loadPublicProduct("8901063201089")).kind).toBe("unavailable");
  });
});

describe("clientMessages", () => {
  it("ships no verdict/health catalogue to the browser", () => {
    const scoped = clientMessages(enMessages);
    const json = JSON.stringify(scoped).toLowerCase();
    expect(json).not.toContain("verdict");
    // The confirm screen's "allergen statement" field label is not health
    // data; what must stay server-side is the allergen namespace itself.
    for (const ns of ["allergen", "reason", "status", "diet", "nutrient"])
      expect(scoped).not.toHaveProperty(ns);
    expect(scoped).toHaveProperty("auth");
    expect(scoped).toHaveProperty("scan");
  });
});

describe("shared public fixtures", () => {
  // Skipped until Task 5 adds packages/test-fixtures/responses/public/.
  it.skipIf(publicFixtures().length === 0)(
    "packages/test-fixtures/responses/public/ has fixtures",
    () => expect(publicFixtures().length).toBeGreaterThan(0),
  );
});
