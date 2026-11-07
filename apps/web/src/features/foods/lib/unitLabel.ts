import type { FoodUnitOut } from "../api/foods";

type T = (key: string, values?: Record<string, string | number>) => string;

const KNOWN_UNITS = new Set([
  "g",
  "ml",
  "serving",
  "piece",
  "piece_small",
  "piece_medium",
  "piece_large",
  "roti",
  "slice",
  "katori",
  "katori_small",
  "katori_medium",
  "katori_large",
  "cup",
  "glass",
  "tbsp",
  "tsp",
]);

/**
 * "katori" / "katoris": the ICU plural of unit.<code> on the count. A code
 * this build does not know shows as the code itself (the API may know more
 * units than this build), like Android.
 */
export function unitLabel(t: T, code: string, count: number): string {
  return KNOWN_UNITS.has(code) ? t(`unit.${code}`, { count }) : code;
}

/** "≈": the grams came through a per-food weight or a density (G-ruling). */
export const APPROX = "≈";
export const isApprox = (source: string | null | undefined): boolean =>
  source === "portion" || source === "density";

/**
 * A unit chip. Any unit with a known size (ml) shows it, like Android (the sizes come from
 * the API: a "medium" katori is smaller than the default one).
 */
export function unitChipLabel(t: T, unit: FoodUnitOut, count = 1): string {
  const base = unitLabel(t, unit.code, count);
  return unit.ml != null && unit.code !== "ml"
    ? `${base} · ${t("unit.ml_hint", { ml: String(unit.ml) })}`
    : base;
}

/** The grams (or ml) line under the chips: always shown, never converted. */
export function amountHint(
  t: T,
  unit: Pick<FoodUnitOut, "code" | "grams_per_unit">,
  basis: "g" | "ml",
): string {
  const label = unitLabel(t, unit.code, 1);
  return basis === "ml"
    ? t("unit.amount_hint_ml", {
        unit: label,
        amount: String(unit.grams_per_unit),
      })
    : t("unit.grams_hint", { unit: label, grams: String(unit.grams_per_unit) });
}
