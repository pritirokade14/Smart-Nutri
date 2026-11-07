import type { FoodUnitOut } from "../api/foods";

type T = (key: string, values?: Record<string, string | number>) => string;

/** "katori" / "katoris": the ICU plural of unit.<code> on the count. */
export function unitLabel(t: T, code: string, count: number): string {
  return t(`unit.${code}`, { count });
}

/**
 * A unit chip. A volume unit with a known size shows it (the sizes come from
 * the API: a "medium" katori is smaller than the default one).
 */
export function unitChipLabel(t: T, unit: FoodUnitOut, count = 1): string {
  const base = unitLabel(t, unit.code, count);
  return unit.kind === "volume" && unit.ml != null
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
