import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { previewPortion } from "@/features/foods/lib/preview";

type Case = {
  case: string;
  per_100: Record<string, number | null>;
  quantity: number;
  expected: {
    error: string | null;
    grams_per_unit: number | null;
    preview: Record<string, number | null> | null;
  };
};
const CASES = (
  JSON.parse(
    readFileSync(
      join(
        process.cwd(),
        "../../packages/test-fixtures/units/conversions.json",
      ),
      "utf8",
    ),
  ) as { cases: Case[] }
).cases;

describe("previewPortion", () => {
  const ok = CASES.filter((c) => c.expected.error === null);
  it("has cases", () => expect(ok.length).toBeGreaterThan(10));

  for (const c of ok)
    it(`matches units/conversions.json: ${c.case}`, () => {
      const got = previewPortion(
        c.per_100,
        c.quantity,
        c.expected.grams_per_unit as number,
      );
      const want = c.expected.preview as Record<string, number | null>;
      for (const [k, v] of Object.entries(want))
        expect(got[k] === null ? null : Number(got[k])).toBe(v);
      // 1 dp strings, null stays null (never "0.0").
      for (const [k, v] of Object.entries(got))
        if (want[k] === null) expect(v).toBeNull();
        else expect(v).toMatch(/^-?\d+\.\d$/);
    });

  it("rounds half up on exact decimals (the 1.15 trap)", () => {
    expect(previewPortion({ fibre_g: 1.15 }, 100, 1).fibre_g).toBe("1.2");
    expect(previewPortion({ fibre_g: 10.016 }, 250, 1).fibre_g).toBe("25.0");
  });

  it("keeps exponent notation exact", () => {
    expect(previewPortion({ a: 1e-7 }, 1, 1).a).toBe("0.0");
    expect(previewPortion({ a: 1e21 }, 1, 1).a).toMatch(/^\d+\.0$/);
  });
});
