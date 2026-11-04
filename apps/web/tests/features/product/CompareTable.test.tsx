import { cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it } from "vitest";
import type { CompareOut } from "@/features/product/api/products";
import { CompareTable } from "@/features/product/components/CompareTable";
import { resultMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";

const en = MESSAGES.en;

const per100 = (o: object) => ({
  energy_kcal: null,
  sugars_g: null,
  salt_g: null,
  sat_fat_g: null,
  protein_g: null,
  fiber_g: null,
  fat_g: null,
  carbs_g: null,
  sodium_mg: null,
  ...o,
});

const data = (): CompareOut => ({
  a: {
    product_id: null,
    barcode: "8901063201089",
    name: "Cream Biscuit",
    brand: "Brand A",
    grade: "D",
    per_100g: per100({
      energy_kcal: 480,
      sugars_g: 30,
      sat_fat_g: 3,
      protein_g: 6,
    }),
    serving_size_g: null,
    protein_per_serving_g: null,
    sugars_per_serving_g: null,
    protein_per_100kcal: null,
    high_in: ["sugar"],
    member_status: "avoid",
    attribution: "attribution.off",
  },
  b: {
    product_id: "d0000000-0000-4000-8000-000000000009",
    barcode: null,
    name: "Oat Biscuit",
    brand: null,
    grade: "B",
    per_100g: per100({
      energy_kcal: 480,
      sugars_g: 8.25,
      salt_g: 0.4,
      sat_fat_g: 5,
      protein_g: 6,
      fiber_g: 7,
    }),
    serving_size_g: null,
    protein_per_serving_g: null,
    sugars_per_serving_g: null,
    protein_per_100kcal: null,
    high_in: [],
    member_status: "unknown",
    attribution: null,
  },
  better: {
    grade: "b",
    energy_kcal: "same",
    sugars_g: "b",
    salt_g: "unknown",
    sat_fat_g: "a",
    protein_g: "same",
    fiber_g: "unknown",
    protein_per_serving_g: "unknown",
    protein_per_100kcal: "unknown",
    sugars_per_serving_g: "unknown",
  },
});

function view(d: CompareOut = data()) {
  return render(
    <NextIntlClientProvider locale="en" messages={resultMessages(en)}>
      <CompareTable data={d} />
    </NextIntlClientProvider>,
  );
}

const row = (key: string) => screen.getByTestId(`row-${key}`);
const cell = (key: string, side: "a" | "b") =>
  within(row(key)).getByTestId(`cell-${side}`);

afterEach(cleanup);

describe("CompareTable", () => {
  it("stacks on narrow viewport: one column, two from the md breakpoint", () => {
    view();
    for (const grid of screen.getAllByTestId("compare-columns")) {
      expect(grid.className).toMatch(/(^|\s)grid-cols-1(\s|$)/);
      expect(grid.className).toMatch(/(^|\s)md:grid-cols-2(\s|$)/);
    }
    // Header plus one per row.
    expect(screen.getAllByTestId("compare-columns")).toHaveLength(11);
  });

  it("marks better side", () => {
    view();
    expect(cell("sugars_g", "b").getAttribute("data-better")).toBe("true");
    expect(
      within(cell("sugars_g", "b")).getByText(en.compare.better_chip),
    ).toBeTruthy();
    expect(cell("sugars_g", "a").getAttribute("data-better")).toBe("false");
    expect(
      within(cell("sugars_g", "a")).queryByText(en.compare.better_chip),
    ).toBeNull();
    expect(cell("sat_fat_g", "a").getAttribute("data-better")).toBe("true");
    expect(cell("grade", "b").getAttribute("data-better")).toBe("true");
    expect(within(row("sugars_g")).getByText(en.compare.better.b)).toBeTruthy();
  });

  it("same and unknown: no side is marked, and the row says why", () => {
    view();
    for (const key of ["energy_kcal", "salt_g", "fiber_g"]) {
      expect(cell(key, "a").getAttribute("data-better")).toBe("false");
      expect(cell(key, "b").getAttribute("data-better")).toBe("false");
    }
    expect(
      within(row("energy_kcal")).getByText(en.compare.better.same),
    ).toBeTruthy();
    expect(
      within(row("salt_g")).getByText(en.compare.better.unknown),
    ).toBeTruthy();
    // A value missing on the label is never shown as 0.
    expect(cell("salt_g", "a").textContent).toContain(en.result.not_on_label);
    expect(cell("salt_g", "a").textContent).not.toMatch(/\b0 g/);
  });

  it("an unexpected better value marks no side", () => {
    const d = data();
    (d.better as Record<string, string>).sugars_g = "both";
    view(d);
    expect(cell("sugars_g", "a").getAttribute("data-better")).toBe("false");
    expect(cell("sugars_g", "b").getAttribute("data-better")).toBe("false");
    expect(
      within(row("sugars_g")).getByText(en.compare.better.unknown),
    ).toBeTruthy();
  });

  it("values per 100 g from the API, the grade calculated by SmartNutri", () => {
    view();
    expect(cell("sugars_g", "b").textContent).toContain("8.3 g");
    expect(cell("energy_kcal", "a").textContent).toContain("480 kcal");
    expect(cell("grade", "a").textContent).toContain("D");
    expect(within(row("grade")).getByText(en.compare.row.grade)).toBeTruthy();
  });

  it("member status exactly as the API sent it; unknown is grey, never ok", () => {
    view();
    const badges = screen.getAllByTestId("verdict-badge");
    expect(badges.map((b) => b.getAttribute("data-verdict"))).toEqual([
      "avoid",
      "unknown",
    ]);
  });

  it("no member: no status badge", () => {
    const d = data();
    d.a.member_status = null;
    d.b.member_status = null;
    view(d);
    expect(screen.queryAllByTestId("verdict-badge")).toHaveLength(0);
  });

  it("credits Open Food Facts for the side that comes from it", () => {
    view();
    const credits = screen.getAllByText(en.attribution.off);
    expect(credits).toHaveLength(1);
    expect(credits[0].closest("a")?.getAttribute("href")).toBe(
      "https://world.openfoodfacts.org/product/8901063201089",
    );
  });
});
