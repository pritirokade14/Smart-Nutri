import { formatAmount } from "@/features/history/lib/summary";
import { APPROX, isApprox, unitLabel } from "./unitLabel";

type T = (key: string, values?: Record<string, string | number>) => string;

/**
 * "2 rotis · 136 g" (or "200 ml" for an ml-basis food) from what the API
 * saved. Grams that came through a per-food weight or a density carry "≈".
 * With no unit (an older row or grams only) it is the amount alone.
 */
export function portionLine(
  t: T,
  p: {
    quantity?: number | null;
    unit?: string | null;
    grams?: number | null;
    basis?: string | null;
    unitSource?: string | null;
  },
): string | null {
  if (p.grams == null) return null;
  const ml = p.basis === "ml";
  const amount = `${isApprox(p.unitSource) ? `${APPROX} ` : ""}${formatAmount(p.grams)}`;
  if (
    p.unit &&
    p.unit !== "g" &&
    !(ml && p.unit === "ml") &&
    p.quantity != null
  ) {
    return t(ml ? "diary.portion_line_ml" : "diary.portion_line", {
      quantity: formatAmount(p.quantity),
      unit: unitLabel(t, p.unit, p.quantity),
      ...(ml ? { amount } : { grams: amount }),
    });
  }
  return ml
    ? t("unit.ml_hint", { ml: amount })
    : t("diary.grams_line", { grams: amount });
}
