import { createTranslator } from "next-intl";
import { describe, expect, it } from "vitest";
import type { FoodUnitOut } from "@/features/foods/api/foods";
import {
  amountHint,
  unitChipLabel,
  unitLabel,
} from "@/features/foods/lib/unitLabel";
import { MESSAGES } from "../../support/analyze-fixtures";

const tr = (locale: "en" | "hi" | "mr") => {
  const t = createTranslator({ locale, messages: MESSAGES[locale] });
  return (k: string, v?: Record<string, string | number>) =>
    t(k as never, v as never) as string;
};
const katori = (code: string, ml: number): FoodUnitOut => ({
  code,
  kind: "volume",
  ml,
  grams_per_unit: 100,
  source: "density",
  user_override: false,
});

describe("unitLabel", () => {
  it("katori sizes show ml", () => {
    const t = tr("en");
    expect(unitChipLabel(t, katori("katori_medium", 155))).toBe(
      "medium katori · 155 ml",
    );
    expect(unitChipLabel(t, katori("katori", 200))).toBe("katori · 200 ml");
  });

  it("a count unit shows no ml", () => {
    const roti: FoodUnitOut = {
      code: "roti",
      kind: "count",
      ml: null,
      grams_per_unit: 68,
      source: "portion_global",
      user_override: false,
    };
    expect(unitChipLabel(tr("en"), roti, 2)).toBe("rotis");
  });

  it("plural forms per locale", () => {
    expect(unitLabel(tr("en"), "katori", 1)).toBe("katori");
    expect(unitLabel(tr("en"), "katori", 2)).toBe("katoris");
    expect(unitLabel(tr("en"), "roti", 2)).toBe("rotis");
    for (const l of ["hi", "mr"] as const) {
      const one = unitLabel(tr(l), "katori", 1);
      expect(one.length).toBeGreaterThan(0);
      expect(one).not.toContain("{");
    }
  });

  it("grams line is the API's number, unrounded", () => {
    expect(amountHint(tr("en"), katori("katori", 200), "g")).toBe(
      "1 katori ≈ 100 g",
    );
    const own = { ...katori("tbsp", 15), grams_per_unit: 13.815 };
    expect(amountHint(tr("en"), own, "g")).toBe("1 tbsp ≈ 13.815 g");
    expect(amountHint(tr("en"), own, "ml")).toContain("13.815 ml");
  });
});
