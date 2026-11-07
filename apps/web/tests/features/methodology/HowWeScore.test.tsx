import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { components } from "@smartnutri/api-client";
import en from "@smartnutri/i18n/messages/en.json";
import hi from "@smartnutri/i18n/messages/hi.json";
import { cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getMethodology } from "@/features/methodology/api/getMethodology";
import { MethodologyView } from "@/features/methodology/components/MethodologyView";
import { clientMessages } from "@/i18n/client-messages";
import { apiStub, envelope, json } from "../../support/api-stub";

type Methodology = components["schemas"]["Methodology"];

const FIXTURE: Methodology = JSON.parse(
  readFileSync(
    join(
      process.cwd(),
      "../../packages/test-fixtures/responses/methodology.json",
    ),
    "utf8",
  ),
);

vi.mock("next-intl/server", () => ({
  setRequestLocale: () => {},
  getTranslations: async ({ locale }: { locale: "en" | "hi" }) => {
    const m = { en, hi }[locale];
    return (key: string) =>
      key
        .split(".")
        .reduce<unknown>((o, k) => (o as Record<string, unknown>)[k], m);
  },
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

let api: ReturnType<typeof apiStub>;
beforeEach(() => {
  fetchMock.mockReset();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

function show(data: Methodology) {
  render(
    <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
      <MethodologyView data={data} />
    </NextIntlClientProvider>,
  );
}

const sectionTitle = (id: string) =>
  (en.methodology.section as Record<string, { title: string }>)[id]?.title;

describe("HowWeScore", () => {
  it("explains the food data and household measures", () => {
    show(FIXTURE);
    const card = screen.getByTestId("methodology-food_data");
    expect(
      within(card).getByRole("heading", {
        name: en.methodology.food_data.title,
      }),
    ).toBeTruthy();
    expect(card.textContent).toContain(en.methodology.food_data.body);
  });

  it("renders every rule from fixture with its threshold and the pending-review banner", () => {
    show(FIXTURE);
    expect(
      screen.getByRole("heading", { level: 1, name: en.methodology.title }),
    ).toBeTruthy();
    expect(screen.getByTestId("pending-review").textContent).toContain(
      en.methodology.pending_review,
    );
    for (const s of FIXTURE.sections) {
      const title = sectionTitle(s.id);
      expect(title, s.id).toBeTruthy();
      const section = screen.getByTestId(`methodology-${s.id}`);
      expect(
        within(section).getByRole("heading", { name: title as string }),
      ).toBeTruthy();
    }
    // Live values from the engine config, rendered as sent.
    const highIn = screen.getByTestId("methodology-high_in");
    expect(within(highIn).getByText("22.5")).toBeTruthy();
    expect(within(highIn).getAllByText("sugars_g").length).toBeGreaterThan(0);
    const bp = screen.getByTestId("methodology-hypertension");
    expect(within(bp).getByText("avoid_salt_g")).toBeTruthy();
    expect(within(bp).getByText("1.5")).toBeTruthy();
    expect(
      screen.getByText(
        en.methodology.version.replace("{version}", FIXTURE.version),
      ),
    ).toBeTruthy();
  });

  it("lets long unbroken keys wrap instead of widening the page", () => {
    show(FIXTURE);
    const codes = document.querySelectorAll("code");
    expect(codes.length).toBeGreaterThan(0);
    for (const c of codes) expect(c.className).toContain("break-all");
  });

  it("labels Nutri-Score as calculated by SmartNutri, never as an FSSAI rating", () => {
    show(FIXTURE);
    const ns = screen.getByTestId("methodology-nutriscore_2023");
    expect(within(ns).getByRole("heading").textContent).toContain(
      "calculated by SmartNutri",
    );
    const text = document.body.textContent ?? "";
    for (const m of text.matchAll(/FSSAI rating/g))
      expect(text.slice(Math.max(0, (m.index ?? 0) - 10), m.index)).toMatch(
        /not an $/,
      );
  });

  it("makes no medical claims and shows the disclaimer", () => {
    show(FIXTURE);
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(/\b(cures?|treats?|treatment|diagnos\w*)\b/i);
    expect(screen.getByText(en.common.disclaimer)).toBeTruthy();
  });

  it("lists sources, links each section to its sources, and flags unverified links", () => {
    show(FIXTURE);
    const list = screen.getByTestId("sources");
    for (const src of FIXTURE.sources) {
      const item = within(list).getByTestId(`source-${src.id}`);
      expect(within(item).getByText(src.title)).toBeTruthy();
      if (src.url) {
        const link = within(item).getByRole("link");
        expect(link.getAttribute("href")).toBe(src.url);
        expect(link.getAttribute("rel")).toContain("nofollow");
      } else {
        expect(within(item).queryByRole("link")).toBeNull();
      }
      if (src.url && !src.url_verified)
        expect(
          within(item).getByText(en.methodology.url_unverified),
        ).toBeTruthy();
    }
    const highIn = screen.getByTestId("methodology-high_in");
    expect(
      within(highIn)
        .getByRole("link", {
          name: "UK FSA front-of-pack guidance (high thresholds)",
        })
        .getAttribute("href"),
    ).toBe("#source-uk_fsa_front_of_pack");
  });

  it("has no pending banner once a clinician signed off, and never says a link is checked unless it is", () => {
    show({
      ...FIXTURE,
      pending_clinician_review: false,
      sources: FIXTURE.sources.map((s, i) => ({ ...s, url_verified: i === 0 })),
    });
    expect(screen.queryByTestId("pending-review")).toBeNull();
    const first = screen.getByTestId(`source-${FIXTURE.sources[0]?.id}`);
    expect(within(first).queryByText(en.methodology.url_unverified)).toBeNull();
  });
});

describe("getMethodology", () => {
  it("fetches GET /v1/methodology in the page language, without a token", async () => {
    api.on("GET", "/v1/methodology", FIXTURE);
    const result = await getMethodology("hi");
    expect(result).toEqual({ kind: "ok", data: FIXTURE });
    const req = fetchMock.mock.calls[0]?.[0] as Request;
    expect(new URL(req.url).searchParams.get("language")).toBe("hi");
    expect(req.headers.get("authorization")).toBeNull();
  });

  it("is unavailable on an error or a network failure (no server text)", async () => {
    api.on("GET", "/v1/methodology", json(429, envelope("rate_limited")));
    expect(await getMethodology("en")).toEqual({ kind: "unavailable" });
    fetchMock.mockRejectedValueOnce(new TypeError("offline"));
    expect(await getMethodology("en")).toEqual({ kind: "unavailable" });
  });
});

describe("how-we-score page", () => {
  it("metadata has the title, description and hreflang alternates", async () => {
    const { generateMetadata } = await import(
      "@/app/[locale]/(public)/how-we-score/page"
    );
    const meta = await generateMetadata({
      params: Promise.resolve({ locale: "hi" }),
    });
    expect(meta.title).toBe(hi.methodology.title);
    expect(meta.description).toBe(hi.methodology.meta_description);
    expect(meta.alternates?.languages).toEqual({
      en: "/en/how-we-score",
      hi: "/hi/how-we-score",
      mr: "/mr/how-we-score",
    });
  });
});
