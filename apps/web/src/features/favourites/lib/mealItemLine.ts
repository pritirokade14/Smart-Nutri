import type { components } from "@smartnutri/api-client";
import { portionLine } from "@/features/foods/lib/portionLine";

type T = (key: string, values?: Record<string, string | number>) => string;

/** A saved meal's item amount: its `grams` read as ml when `basis` is "ml". */
export function mealItemAmount(
  t: T,
  item: components["schemas"]["FavouriteItemOut"],
): string | null {
  return portionLine(t, {
    quantity: item.quantity,
    unit: item.unit,
    grams: item.grams,
    basis: item.basis,
  });
}
