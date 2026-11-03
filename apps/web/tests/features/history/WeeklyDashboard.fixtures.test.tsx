import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it } from "vitest";
import { WeeklyDashboard } from "@/features/history/components/WeeklyDashboard";
import type { Summary } from "@/features/meals/api/meals";
import { clientMessages } from "@/i18n/client-messages";
import {
  LOCALES,
  MESSAGES,
  type TestLocale,
} from "../../support/analyze-fixtures";

const FIXTURE = join(
  process.cwd(),
  "../../packages/test-fixtures/meals/expected/week_family.dad_diabetic.json",
);
const golden = (): Summary => JSON.parse(readFileSync(FIXTURE, "utf8"));

function view(summary: Summary, locale: TestLocale = "en") {
  return render(
    <NextIntlClientProvider
      locale={locale}
      messages={clientMessages(MESSAGES[locale])}
    >
      <WeeklyDashboard summary={summary} />
    </NextIntlClientProvider>,
  );
}

const en = MESSAGES.en;
const section = (key: string) => screen.getByTestId(`nutrient-${key}`);
const bars = (key: string) => within(section(key)).getAllByTestId("day-bar");
const bar = (key: string, date: string) =>
  bars(key).find((b) => b.getAttribute("data-date") === date) as HTMLElement;

afterEach(cleanup);

describe("WeeklyDashboard (week_family, Dad)", () => {
  it("renders 7 day bars per nutrient, oldest first", () => {
    view(golden());
    for (const key of ["sugars_g", "salt_g", "protein_g", "energy_kcal"]) {
      const b = bars(key);
      expect(b).toHaveLength(7);
      expect(b.map((x) => x.getAttribute("data-date"))).toEqual(
        golden().days.map((d) => d.date),
      );
    }
  });

  it("the over band (token variable) is on the right day", () => {
    view(golden());
    const over = bar("sugars_g", "2026-10-31");
    expect(over.getAttribute("data-band")).toBe("over");
    const fill = within(over).getByTestId("bar-fill");
    expect(fill.className).toContain("bg-(--band-color)");
    // Only that day is over for sugar.
    expect(
      bars("sugars_g").filter((b) => b.getAttribute("data-band") === "over"),
    ).toHaveLength(1);
    expect(bar("sugars_g", "2026-11-03").getAttribute("data-band")).toBe("ok");
  });

  it("shows the incomplete note, the limits note and the sugar note", () => {
    view(golden());
    expect(screen.getByText(en.summary.incomplete)).toBeTruthy();
    expect(screen.getByText(en.summary.limits_note)).toBeTruthy();
    expect(screen.getByText(en.summary.sugar_note)).toBeTruthy();
    expect(screen.getByText(en.summary.week_note)).toBeTruthy();
  });

  it("the week's sugar band is the API's over (a day was over, ruling M1 B1)", () => {
    view(golden());
    expect(golden().bands.sugar_g).toBe("over");
    const badge = within(section("sugars_g")).getByTestId("band-badge");
    expect(badge.getAttribute("data-band")).toBe("over");
    expect(badge.textContent).toContain(en.summary.band.over);
    const salt = within(section("salt_g")).getByTestId("band-badge");
    expect(salt.getAttribute("data-band")).toBe("ok");
    expect(salt.textContent).toContain(en.summary.band.ok);
  });

  it("a day whose only item has no sugar value is unknown, never 0 g", () => {
    view(golden());
    const day = bar("sugars_g", "2026-11-01");
    expect(day.getAttribute("data-band")).toBe("unknown");
    expect(day.textContent).toContain(en.summary.band.unknown);
    expect(day.textContent).not.toMatch(/\b0 g/);
  });

  it("a day with nothing logged says so and is never banded ok", () => {
    view(golden());
    const empty = bar("sugars_g", "2026-10-30");
    expect(empty.getAttribute("data-band")).toBe("unknown");
    expect(empty.textContent).toContain(en.summary.nothing_logged);
    expect(empty.textContent).not.toMatch(/\b0 g/);
  });

  it("protein is neutral progress: no band and never 'Within limit'", () => {
    view(golden());
    const protein = section("protein_g");
    expect(protein.textContent).not.toContain(en.summary.band.ok);
    expect(within(protein).queryByTestId("band-badge")).toBeNull();
    for (const b of bars("protein_g"))
      expect(b.hasAttribute("data-band")).toBe(false);
    const kcal = section("energy_kcal");
    expect(within(kcal).queryByTestId("band-badge")).toBeNull();
    expect(kcal.textContent).toContain(en.summary.kcal_info);
  });

  it("week totals are shown as plain totals (never against a daily limit)", () => {
    view(golden());
    expect(section("salt_g").textContent).toContain("1.7 g");
    expect(section("salt_g").textContent).not.toContain("1.7 g of 5 g");
  });

  it.each(LOCALES)(
    "renders in %s with every string from the catalogue",
    (l) => {
      view(golden(), l);
      const m = MESSAGES[l];
      expect(screen.getByText(m.summary.limits_note)).toBeTruthy();
      expect(screen.getByText(m.summary.incomplete)).toBeTruthy();
      expect(screen.getByText(m.summary.title.week)).toBeTruthy();
    },
  );
});

describe("WeeklyDashboard: nullable totals and the unknown protein band (Ruling M1)", () => {
  function nulled(): Summary {
    const s = golden() as unknown as {
      totals: Record<string, number | null>;
      bands: Record<string, string>;
      days: {
        totals: Record<string, number | null>;
        items: number;
        bands: Record<string, string>;
      }[];
    };
    s.totals.sugars_g = null;
    s.totals.protein_g = null;
    for (const d of s.days) {
      if (d.items === 0) {
        for (const k of Object.keys(d.totals)) d.totals[k] = null;
      }
    }
    s.days[4].totals.sugars_g = null;
    // Even if a band said ok for a null total, the UI must not show it as fine.
    s.days[4].bands.sugar_g = "ok";
    s.bands.protein_g = "unknown";
    return s as unknown as Summary;
  }

  it("a null total is 'Not enough data', never 0", () => {
    view(nulled());
    const sugar = section("sugars_g");
    expect(within(sugar).getByTestId("week-total").textContent).toBe(
      en.summary.band.unknown,
    );
    expect(sugar.textContent).not.toMatch(/\b0 g/);
    const protein = section("protein_g");
    expect(within(protein).getByTestId("week-total").textContent).toBe(
      en.summary.band.unknown,
    );
  });

  it("a null day total is never banded ok (shown grey)", () => {
    view(nulled());
    const day = bar("sugars_g", "2026-11-01");
    expect(day.getAttribute("data-band")).toBe("unknown");
    expect(day.textContent).toContain(en.summary.band.unknown);
  });

  it("protein band unknown never reads 'Within limit'", () => {
    view(nulled());
    expect(section("protein_g").textContent).not.toContain(en.summary.band.ok);
  });

  it("an unexpected band value renders as unknown, never ok", () => {
    const s = golden() as unknown as { bands: Record<string, string> };
    s.bands.salt_g = "fine";
    view(s as unknown as Summary);
    const badge = within(section("salt_g")).getByTestId("band-badge");
    expect(badge.getAttribute("data-band")).toBe("unknown");
  });

  it("a missing totals field (older or newer API) is unknown", () => {
    const s = golden() as unknown as { totals: Record<string, unknown> };
    delete s.totals.salt_g;
    view(s as unknown as Summary);
    expect(
      within(section("salt_g")).getByTestId("week-total").textContent,
    ).toBe(en.summary.band.unknown);
  });
});
