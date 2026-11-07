import en from "@smartnutri/i18n/messages/en.json";
import { createTranslator } from "next-intl";
import { describe, expect, it } from "vitest";
import { mealItemAmount } from "@/features/favourites/lib/mealItemLine";

const t = createTranslator({ locale: "en", messages: en }) as unknown as (
  k: string,
  v?: Record<string, string | number>,
) => string;
const base = { name: "x", source_kind: "food" as const, attributions: [] };

describe("mealItemAmount", () => {
  it("shows ml for an ml-basis item", () => {
    const s = mealItemAmount(t, {
      ...base,
      quantity: null,
      unit: null,
      grams: 200,
      basis: "ml",
    });
    expect(s).toContain("200");
    expect(s).toContain("ml");
    expect(s).not.toMatch(/\bg\b/);
  });
  it("shows g for a gram-basis item", () => {
    const s = mealItemAmount(t, {
      ...base,
      quantity: null,
      unit: null,
      grams: 136,
      basis: "g",
    });
    expect(s).toMatch(/136 ?g/);
  });
});
