import type { components } from "@smartnutri/api-client";
import type { Translator } from "./reasons";

// Readers for the parts of the untyped `report` object (and the product) that
// the logged-in result renders. They only read and label what the API sent;
// nothing here decides or changes a result.

export type ClaimVerdict = "supported" | "contradicted" | "unverifiable";
export type ClaimCheck = {
  claim: string;
  verdict: ClaimVerdict;
  reason_code: string;
  params: Record<string, unknown>;
};

const CLAIM_VERDICTS = new Set<string>([
  "supported",
  "contradicted",
  "unverifiable",
]);

/** `report.claims`, dropping any entry that is not a well-formed check. */
export function readClaims(report: Record<string, unknown>): ClaimCheck[] {
  if (!Array.isArray(report.claims)) return [];
  const out: ClaimCheck[] = [];
  for (const c of report.claims as unknown[]) {
    if (typeof c !== "object" || c === null) continue;
    const { claim, verdict, reason_code, params } = c as Record<
      string,
      unknown
    >;
    if (
      typeof claim !== "string" ||
      typeof verdict !== "string" ||
      !CLAIM_VERDICTS.has(verdict) ||
      typeof reason_code !== "string"
    )
      continue;
    out.push({
      claim,
      verdict: verdict as ClaimVerdict,
      reason_code,
      params:
        typeof params === "object" && params !== null
          ? (params as Record<string, unknown>)
          : {},
    });
  }
  return out;
}

// Latin digits, up to 3 decimals, in every locale (as for member reasons).
const NUMBER = new Intl.NumberFormat("en", { maximumFractionDigits: 3 });
const SAFE_CODE = /^[a-z0-9_]+$/;

/**
 * `claim_reason.<code>` with its params, or null when this build does not
 * know the code or the params do not fit (then no reason line is shown).
 * Same rules as Android's claimReasonText.
 */
export function claimReasonText(t: Translator, c: ClaimCheck): string | null {
  const p = c.params;
  const num = (k: string) =>
    typeof p[k] === "number" && Number.isFinite(p[k])
      ? NUMBER.format(p[k] as number)
      : null;
  const list = (k: string) => {
    const v = p[k];
    return Array.isArray(v) &&
      v.length > 0 &&
      v.every((x) => typeof x === "string")
      ? (v as string[]).join(", ")
      : null;
  };
  const nutrient = (k: string) => {
    const v = p[k];
    return typeof v === "string" && SAFE_CODE.test(v) && t.has(`nutrient.${v}`)
      ? t(`nutrient.${v}`)
      : null;
  };
  const key = `claim_reason.${c.reason_code}`;
  let values: Record<string, string> | null;
  switch (c.reason_code) {
    case "ok":
    case "ingredients_unknown":
    case "no_standard":
      values = {};
      break;
    case "exceeds_limit":
    case "below_minimum": {
      const limit = num("limit");
      const value = num("value");
      values = limit && value ? { limit, value } : null;
      break;
    }
    case "nutrient_missing": {
      const n = nutrient("nutrient");
      values = n ? { nutrient: n } : null;
      break;
    }
    case "whey_not_listed":
    case "basis_unknown":
      values = {};
      break;
    case "below_claimed": {
      // "{value} g ... {basis, select, per_serving {...} other {...}}"
      const value = num("value");
      const claimed = num("claimed");
      const basis =
        p.basis === "per_serving" || p.basis === "per_100g" ? p.basis : null;
      values = value && claimed && basis ? { value, claimed, basis } : null;
      break;
    }
    case "other_protein_source":
    case "added_sugar_ingredient":
    case "refined_sugar_ingredient": {
      const i = list("ingredients");
      values = i ? { ingredients: i } : null;
      break;
    }
    default:
      values = null;
  }
  if (values === null || !t.has(key)) return null;
  return t(key, values);
}

export type NutrientsOut = components["schemas"]["NutrientsOut"];

/** The per-100 g/ml rows, in engine order, with their confirm.field labels. */
export const NUTRITION_ROWS = [
  "energy_kcal",
  "protein_g",
  "carbs_g",
  "sugars_g",
  "fat_g",
  "sat_fat_g",
  "fiber_g",
  "salt_g",
  "sodium_mg",
] as const satisfies readonly (keyof NutrientsOut)[];

/**
 * A nutrient amount as the API sent it (Latin digits, no rounding beyond
 * float noise; same as Android's formatForDisplay). Null stays null: a value
 * the label does not show is never displayed as 0.
 */
export function formatAmount(v: number | null | undefined): string | null {
  if (typeof v !== "number" || !Number.isFinite(v)) return null;
  return String(Number(v.toPrecision(12)));
}
