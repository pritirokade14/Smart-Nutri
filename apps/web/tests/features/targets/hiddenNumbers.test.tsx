import { cleanup, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it } from "vitest";
import { DayTotals } from "@/features/history/components/DayTotals";
import { WeeklyDashboard } from "@/features/history/components/WeeklyDashboard";
import type { DaySummary, Summary } from "@/features/meals/api/meals";
import { ProteinProgress } from "@/features/protein/components/ProteinProgress";
import { MESSAGES } from "../../support/analyze-fixtures";

const en = MESSAGES.en;
const PRIMARY = "a0000000-0000-4000-8000-000000000001";

const day = (date: string, hidden: boolean): DaySummary => ({
  date,
  items: 2,
  totals: hidden
    ? { energy_kcal: null, sugars_g: null, salt_g: null, protein_g: null }
    : { energy_kcal: 900, sugars_g: 20, salt_g: 3, protein_g: 40 },
  incomplete: {
    energy_kcal: false,
    sugars_g: false,
    salt_g: false,
    protein_g: false,
  },
  bands: { kcal: "unknown", protein_g: "ok", salt_g: "near", sugar_g: "ok" },
});

const summary = (over: Partial<Summary> = {}): Summary => ({
  member_id: PRIMARY,
  period: "day",
  start: "2026-11-07",
  end: "2026-11-07",
  totals: { energy_kcal: 900, sugars_g: 20, salt_g: 3, protein_g: 40 },
  incomplete: {
    energy_kcal: false,
    sugars_g: false,
    salt_g: false,
    protein_g: false,
  },
  limits: {
    kcal: null,
    protein_target_g: 112,
    protein_g_per_kg: 1.6,
    protein_basis: "actual_weight",
    protein_target_status: null,
    salt_g: 5,
    sugar_g: 25,
  },
  bands: { kcal: "unknown", protein_g: "ok", salt_g: "ok", sugar_g: "near" },
  days: [day("2026-11-07", false)],
  pending_clinician_review: true,
  protein_left_g: 72,
  numbers_hidden: { energy: false, macros: false },
  ...over,
});

const HIDDEN: Partial<Summary> = {
  totals: { energy_kcal: null, sugars_g: null, salt_g: null, protein_g: null },
  protein_left_g: null,
  limits: {
    kcal: null,
    protein_target_g: null,
    protein_g_per_kg: null,
    protein_basis: null,
    protein_target_status: null,
    salt_g: 5,
    sugar_g: 25,
  },
  days: [day("2026-11-07", true)],
  numbers_hidden: { energy: true, macros: true },
};

afterEach(cleanup);
const wrap = (ui: ReactNode) =>
  render(
    <NextIntlClientProvider locale="en" messages={en}>
      {ui}
    </NextIntlClientProvider>,
  );

describe("hidden numbers", () => {
  it("history day hides totals when numbers_hidden", () => {
    wrap(<DayTotals summary={summary(HIDDEN)} />);
    const values = screen.getAllByTestId("day-value");
    expect(values).toHaveLength(4);
    for (const v of values) {
      expect(v.textContent).toBe(en.diary.hidden_numbers);
      expect(v.textContent).not.toBe(en.summary.band.unknown);
    }
    expect(screen.getByTestId("day-totals").textContent).not.toMatch(/\d/);
  });

  it("history week hides totals when numbers_hidden", () => {
    wrap(
      <WeeklyDashboard
        summary={summary({
          ...HIDDEN,
          period: "week",
          days: ["2026-11-06", "2026-11-07"].map((d) => day(d, true)),
        })}
      />,
    );
    for (const t of screen.getAllByTestId("week-total"))
      expect(t.textContent).toBe(en.diary.hidden_numbers);
    expect(screen.queryByText(/kcal/)).toBeNull();
  });

  it("hide_energy hides only calories in History", () => {
    wrap(
      <DayTotals
        summary={summary({
          totals: {
            energy_kcal: null,
            sugars_g: 20,
            salt_g: 3,
            protein_g: 40,
          },
          numbers_hidden: { energy: true, macros: false },
        })}
      />,
    );
    expect(screen.getByTestId("day-energy_kcal").textContent).toContain(
      en.diary.hidden_numbers,
    );
    expect(screen.getByTestId("day-protein_g").textContent).toContain("40 g");
  });

  it("protein card hides every number when macros are hidden", () => {
    wrap(<ProteinProgress summary={summary(HIDDEN)} locale="en" />);
    const card = screen.getByTestId("protein-progress");
    expect(card.textContent).toContain(en.diary.hidden_numbers);
    expect(card.textContent).not.toMatch(/\d/);
    expect(card.textContent).not.toContain(en.summary.band.unknown);
  });

  it("protein card lean basis copy", () => {
    wrap(
      <ProteinProgress
        summary={summary({
          limits: {
            kcal: null,
            protein_target_g: 119,
            protein_g_per_kg: 2,
            protein_basis: "lean_mass",
            protein_target_status: "ready",
            salt_g: 5,
            sugar_g: 25,
          },
        })}
        locale="en"
      />,
    );
    expect(
      screen.getByText(
        en.protein.guide_lean
          .replace("{target}", "119")
          .replace("{per_kg}", "2"),
      ),
    ).toBeTruthy();
  });

  it("protein card adjusted-weight basis copy", () => {
    wrap(
      <ProteinProgress
        summary={summary({
          limits: {
            kcal: null,
            protein_target_g: 71,
            protein_g_per_kg: 1.2,
            protein_basis: "adjusted_weight",
            protein_target_status: "ready",
            salt_g: 5,
            sugar_g: 25,
          },
        })}
        locale="en"
      />,
    );
    expect(
      screen.getByText(
        en.protein.guide_adjusted
          .replace("{target}", "71")
          .replace("{per_kg}", "1.2"),
      ),
    ).toBeTruthy();
  });

  it("protein card paused for pregnancy", () => {
    wrap(
      <ProteinProgress
        summary={summary({
          limits: {
            kcal: null,
            protein_target_g: null,
            protein_g_per_kg: null,
            protein_basis: null,
            protein_target_status: "paused_pregnancy",
            salt_g: 5,
            sugar_g: 25,
          },
          protein_left_g: null,
        })}
        locale="en"
      />,
    );
    expect(screen.getByText(en.targets.pregnancy.paused)).toBeTruthy();
    expect(screen.queryByText(en.protein.no_target)).toBeNull();
  });
});
