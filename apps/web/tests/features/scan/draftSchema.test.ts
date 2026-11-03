import { describe, expect, it } from "vitest";
import {
  type DraftFormValues,
  draftSchema,
  isDraftConfirm,
  NUTRIENT_FIELDS,
  type NumberInput,
  type NutrientField,
  parseNumberInput,
} from "@/features/scan/lib/draftSchema";
import { highlightedFields, parseWarning } from "@/features/scan/lib/warnings";
import { draftCaseFiles, draftFile } from "../../support/drafts";

function formWith(
  nutrients: Partial<Record<NutrientField, NumberInput>> = {},
  rest: Partial<DraftFormValues> = {},
): DraftFormValues {
  const all = Object.fromEntries(
    NUTRIENT_FIELDS.map((f) => [f, "1"]),
  ) as Record<NutrientField, NumberInput>;
  return {
    scan_id: "0b6c1f8e-3c1a-4f0e-9a51-1d2e3f4a5b6c",
    barcode: "8901063201089",
    name: "Oats",
    brand: "",
    category: "general",
    basis: "per_100g",
    sodium_unit: "",
    nutrients: { ...all, ...nutrients },
    serving_size_g: null,
    ingredients: [],
    allergen_statement: "",
    may_contain_statement: "",
    claims: [],
    veg_mark: "",
    confirmed_fields: [],
    ...rest,
  };
}

describe("draftSchema", () => {
  it("empty numeric inputs parse to null, not 0", () => {
    expect(
      draftSchema.parse(formWith({ fiber_g: "" })).nutrients.fiber_g,
    ).toBeNull();
    expect(
      draftSchema.parse(formWith({ fiber_g: "   " })).nutrients.fiber_g,
    ).toBeNull();
    expect(
      draftSchema.parse(formWith({ fiber_g: null })).nutrients.fiber_g,
    ).toBeNull();
  });

  it("sends numbers exactly as printed: no rounding, no unit arithmetic", () => {
    const body = draftSchema.parse(
      formWith(
        { sodium_mg: "0.4", protein_g: 6.666666666666667, sugars_g: "12.345" },
        { sodium_unit: "g" },
      ),
    );
    expect(body.nutrients.sodium_mg).toBe(0.4);
    expect(body.sodium_unit).toBe("g");
    expect(body.nutrients.protein_g).toBe(6.666666666666667);
    expect(body.nutrients.sugars_g).toBe(12.345);
  });

  it("sodium_unit is null unless the user picked one (never defaulted to mg)", () => {
    expect(draftSchema.parse(formWith()).sodium_unit).toBeNull();
  });

  it("rejects text, negatives and commas as numbers instead of guessing", () => {
    for (const bad of ["abc", "-1", "1,5", "1.2.3"]) {
      const r = draftSchema.safeParse(formWith({ sugars_g: bad }));
      expect(r.success).toBe(false);
      if (!r.success)
        expect(r.issues).toContainEqual({
          field: "sugars_g",
          code: "invalid_number",
        });
    }
    expect(parseNumberInput(".5")).toBe(0.5);
    expect(parseNumberInput("0")).toBe(0);
  });

  it("requires a name, a category and a basis; nothing defaults", () => {
    const r = draftSchema.safeParse(
      formWith({}, { name: " ", category: "", basis: "" }),
    );
    expect(r.success).toBe(false);
    if (!r.success)
      expect(r.issues.map((i) => i.field).sort()).toEqual([
        "basis",
        "category",
        "name",
      ]);
  });

  it("per_serving needs a serving size", () => {
    const r = draftSchema.safeParse(
      formWith({}, { basis: "per_serving", serving_size_g: "" }),
    );
    expect(r.success).toBe(false);
    const ok = draftSchema.parse(
      formWith({}, { basis: "per_serving", serving_size_g: "30" }),
    );
    expect(ok.basis).toBe("per_serving");
    expect(ok.serving_size_g).toBe(30);
  });

  it("manual entry omits scan_id and sends no confirmed_fields", () => {
    const body = draftSchema.parse(
      formWith({}, { scan_id: null, confirmed_fields: ["protein_g"] }),
    );
    expect("scan_id" in body).toBe(false);
    expect(body.confirmed_fields).toEqual([]);
  });

  it("Devanagari text round-trips unchanged", () => {
    const ingredients = ["बेसन (चने का आटा)", "मूँगफली", "नमक"];
    const body = draftSchema.parse(
      formWith(
        {},
        {
          name: "नमकीन मिक्स",
          ingredients,
          allergen_statement: "इसमें मूँगफली है।",
        },
      ),
    );
    expect(body.ingredients).toEqual(ingredients);
    expect(body.name).toBe("नमकीन मिक्स");
    expect(body.allergen_statement).toBe("इसमें मूँगफली है।");
  });

  it("a blank statement is sent as null", () => {
    const body = draftSchema.parse(formWith({}, { allergen_statement: "  " }));
    expect(body.allergen_statement).toBeNull();
  });
});

describe("warnings", () => {
  it("splits code:path into the i18n code, the field and the column", () => {
    expect(parseWarning("unit_unconfirmed:per_100g.sodium_mg")).toEqual({
      raw: "unit_unconfirmed:per_100g.sodium_mg",
      code: "unit_unconfirmed",
      path: "per_100g.sodium_mg",
      field: "sodium_mg",
      column: "per_100g",
    });
    expect(parseWarning("implausible_value:sugars_g").field).toBe("sugars_g");
    expect(parseWarning("low_confidence")).toMatchObject({
      code: "low_confidence",
      field: null,
    });
  });

  it("highlights the fields named by field-level warnings", () => {
    expect([
      ...highlightedFields([
        "implausible_value:sugars_g",
        "unreadable_field:per_100g.fat_g",
        "upper_bound:per_100g.protein_g",
        "unit_unconfirmed:per_serving.sodium_mg",
        "low_confidence",
        "category_check",
      ]),
    ]).toEqual(["sugars_g", "fat_g", "protein_g", "sodium_mg"]);
  });
});

describe("isDraftConfirm (draft.confirm, R21)", () => {
  const col = {
    printed: true,
    shared: false,
    sodium_unit_required: false,
    confirm_fields: ["protein_g", "serving_size_g"],
  };
  const ok = {
    basis_required: false,
    category_required: true,
    columns: { per_100g: col, per_serving: null },
  };

  it("accepts every shared fixture draft's hints", () => {
    for (const f of draftCaseFiles())
      expect(isDraftConfirm(draftFile(f).confirm)).toBe(true);
  });

  it("accepts a well-formed hint", () => {
    expect(isDraftConfirm(ok)).toBe(true);
  });

  it.each([
    ["missing", undefined],
    ["null", null],
    [
      "no bases offered",
      { ...ok, columns: { per_100g: null, per_serving: null } },
    ],
    ["non-boolean flag", { ...ok, basis_required: "no" }],
    [
      "unknown confirm field",
      {
        ...ok,
        columns: {
          per_100g: { ...col, confirm_fields: ["name"] },
          per_serving: null,
        },
      },
    ],
    [
      "column without printed",
      {
        ...ok,
        columns: {
          per_100g: { ...col, printed: undefined },
          per_serving: null,
        },
      },
    ],
  ])("rejects %s", (_, v) => {
    expect(isDraftConfirm(v)).toBe(false);
  });
});

describe("draftSchema: scan body shape", () => {
  it("no barcode → no barcode key (as in the shared fixtures)", () => {
    const body = draftSchema.parse(formWith({}, { barcode: null }));
    expect("barcode" in body).toBe(false);
  });

  it("confirmed_fields go out once each, in contract order", () => {
    const body = draftSchema.parse(
      formWith(
        {},
        { confirmed_fields: ["serving_size_g", "protein_g", "protein_g"] },
      ),
    );
    expect(body.confirmed_fields).toEqual(["protein_g", "serving_size_g"]);
  });
});
