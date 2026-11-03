import type { components } from "@smartnutri/api-client";

export type ProductCreate = components["schemas"]["ProductCreate"];
export type PrintedNutrients = components["schemas"]["PrintedNutrients"];
export type ProductDraft = components["schemas"]["ProductDraft"];
export type DraftNutrients = components["schemas"]["DraftNutrients"];
export type ScanDraftOut = components["schemas"]["ScanDraftOut"];
export type Category = ProductCreate["category"];
export type Basis = ProductCreate["basis"];
export type SodiumUnit = NonNullable<ProductCreate["sodium_unit"]>;
export type VegMark = NonNullable<ProductCreate["veg_mark"]>;
export type ConfirmableField = NonNullable<
  ProductCreate["confirmed_fields"]
>[number];

/** The nine fields the rules engine reads, in engine order. */
export const ENGINE_FIELDS = [
  "energy_kcal",
  "protein_g",
  "carbs_g",
  "sugars_g",
  "fat_g",
  "sat_fat_g",
  "fiber_g",
  "salt_g",
  "sodium_mg",
] as const;
export type EngineField = (typeof ENGINE_FIELDS)[number];

/** Every nutrient row on the confirm screen, in display order. */
export const NUTRIENT_FIELDS = [
  "energy_kcal",
  "protein_g",
  "carbs_g",
  "sugars_g",
  "added_sugars_g",
  "fat_g",
  "sat_fat_g",
  "trans_fat_g",
  "fiber_g",
  "salt_g",
  "sodium_mg",
] as const;
export type NutrientField = (typeof NUTRIENT_FIELDS)[number];

export const CATEGORIES: readonly Category[] = [
  "general",
  "beverage",
  "water",
  "cheese",
  "fat",
];
export const BASES: readonly Basis[] = ["per_100g", "per_serving"];
export const SODIUM_UNITS: readonly SodiumUnit[] = ["mg", "g"];

/**
 * A number field as the form holds it: the draft's original number while the
 * user has not touched it (sent exactly, never rounded), the typed text once
 * they have, or null when the pack prints nothing.
 */
export type NumberInput = number | string | null;

/** Raw form values. `draftSchema` turns them into the API body. */
export type DraftFormValues = {
  /** The label scan this came from; null or absent for manual entry. */
  scan_id?: string | null;
  barcode?: string | null;
  name: string;
  brand: string;
  category: Category | "";
  basis: Basis | "";
  sodium_unit: SodiumUnit | "";
  nutrients: Record<NutrientField, NumberInput>;
  serving_size_g: NumberInput;
  ingredients: string[];
  allergen_statement: string;
  may_contain_statement: string;
  claims: string[];
  veg_mark: VegMark | "";
  confirmed_fields: ConfirmableField[];
};

export type DraftIssue = {
  /** A form field: a nutrient key, serving_size_g, name, category or basis. */
  field: string;
  code: "required" | "invalid_number";
};

export type DraftParseResult =
  | { success: true; data: ProductCreate }
  | { success: false; issues: DraftIssue[] };

export class DraftParseError extends Error {
  constructor(public readonly issues: DraftIssue[]) {
    super("draft_invalid");
    this.name = "DraftParseError";
  }
}

const DECIMAL = /^(\d+(\.\d*)?|\.\d+)$/;

/**
 * "" → null (blank stays blank, never 0); a plain non-negative decimal → that
 * number, unrounded; anything else → undefined (invalid).
 */
export function parseNumberInput(v: NumberInput): number | null | undefined {
  if (v === null) return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : undefined;
  const s = v.trim();
  if (s === "") return null;
  if (!DECIMAL.test(s)) return undefined;
  const n = Number(s);
  return Number.isFinite(n) ? n : undefined;
}

function blankToNull(s: string): string | null {
  const t = s.trim();
  return t === "" ? null : t;
}

function safeParse(v: DraftFormValues): DraftParseResult {
  const issues: DraftIssue[] = [];
  const num = (field: string, input: NumberInput): number | null => {
    const n = parseNumberInput(input);
    if (n === undefined) {
      issues.push({ field, code: "invalid_number" });
      return null;
    }
    return n;
  };

  const nutrients = {} as Record<NutrientField, number | null>;
  for (const f of NUTRIENT_FIELDS) nutrients[f] = num(f, v.nutrients[f]);
  const serving = num("serving_size_g", v.serving_size_g);

  const name = v.name.trim();
  if (name === "") issues.push({ field: "name", code: "required" });
  if (v.category === "") issues.push({ field: "category", code: "required" });
  if (v.basis === "") issues.push({ field: "basis", code: "required" });
  if (
    v.basis === "per_serving" &&
    serving === null &&
    !issues.some((i) => i.field === "serving_size_g")
  ) {
    issues.push({ field: "serving_size_g", code: "required" });
  }
  if (issues.length > 0 || v.category === "" || v.basis === "") {
    return { success: false, issues };
  }

  const isScan = typeof v.scan_id === "string" && v.scan_id !== "";
  const body: ProductCreate = {
    ...(isScan ? { scan_id: v.scan_id } : {}),
    barcode: v.barcode ?? null,
    name,
    brand: blankToNull(v.brand),
    category: v.category,
    basis: v.basis,
    nutrients,
    sodium_unit: v.sodium_unit === "" ? null : v.sodium_unit,
    serving_size_g: serving,
    // Sent as typed: Devanagari stays Devanagari, nothing is dropped here.
    ingredients: [...v.ingredients],
    allergen_statement: blankToNull(v.allergen_statement),
    may_contain_statement: blankToNull(v.may_contain_statement),
    claims: v.claims.map((c) => c.trim()).filter((c) => c !== ""),
    veg_mark: v.veg_mark === "" ? null : v.veg_mark,
    // Manual entry: every value is typed by the user, nothing to confirm.
    confirmed_fields: isScan ? [...new Set(v.confirmed_fields)] : [],
  };
  return { success: true, data: body };
}

/**
 * Form values → the `POST /v1/products` body. No nutrient arithmetic: the
 * numbers go out exactly as printed (or typed), with the user's explicit
 * basis and sodium-unit choices; the server converts.
 */
export const draftSchema = {
  safeParse,
  parse(v: DraftFormValues): ProductCreate {
    const r = safeParse(v);
    if (!r.success) throw new DraftParseError(r.issues);
    return r.data;
  },
};
