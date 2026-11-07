"use client";

import { useTranslations } from "next-intl";
import { chipClass } from "@/components/ui/Chip";
import { formatAmount } from "@/features/history/lib/summary";
import type { RecipeOut } from "../api/recipes";

// Existing catalogue keys, in display order.
const ROWS = [
  ["energy_kcal", "confirm.field.energy_kcal", "energy"],
  ["protein_g", "confirm.field.protein_g", "macros"],
  ["carbs_g", "confirm.field.carbs_g", "macros"],
  ["fat_g", "confirm.field.fat_g", "macros"],
  ["sugars_g", "confirm.field.sugars_g", "macros"],
  ["sat_fat_g", "confirm.field.sat_fat_g", "macros"],
  ["fibre_g", "confirm.field.fiber_g", "macros"],
  ["salt_g", "confirm.field.salt_g", "macros"],
] as const;

type Snapshot = RecipeOut["per_100g"];

/**
 * A recipe's nutrients exactly as the API sums them. A key in
 * `incomplete_nutrients` is a lower bound: "At least X" with the grey
 * incomplete marker, never a plain number and never green. A null is "Not
 * known". Hidden numbers draw nothing at all (no digits).
 */
export function RecipeNutrients({ recipe }: { recipe: RecipeOut }) {
  const t = useTranslations();
  const hidden = recipe.numbers_hidden;
  const rows = ROWS.filter(([, , group]) => !hidden[group]);
  if (rows.length === 0) return null;
  const incomplete = new Set(recipe.incomplete_nutrients);
  const block = (title: string, snap: Snapshot, testId: string) => (
    <section className="space-y-1" data-testid={testId}>
      <h3 className="text-sm font-semibold text-text-secondary">{title}</h3>
      <dl className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 text-sm">
        {rows.map(([key, label]) => {
          const v = snap[key];
          const unit =
            key === "energy_kcal" ? "targets.kcal_value" : "targets.g_value";
          const shown = v == null ? null : t(unit, { value: formatAmount(v) });
          const partial = incomplete.has(key);
          return (
            <div key={key} className="contents">
              <dt className="text-text-secondary">{t(label)}</dt>
              <dd
                data-testid={`${testId}-${key}`}
                className="flex flex-wrap items-center justify-end gap-2 text-text-primary"
                data-allow-digits
              >
                {shown === null ? (
                  t("foods.not_known")
                ) : partial ? (
                  <>
                    {t("diary.week.at_least", { value: shown })}
                    <span
                      className={chipClass}
                      data-testid={`${testId}-${key}-incomplete`}
                    >
                      {t("recipes.incomplete")}
                    </span>
                  </>
                ) : (
                  shown
                )}
              </dd>
            </div>
          );
        })}
      </dl>
    </section>
  );
  return (
    <div className="space-y-3" data-testid="recipe-nutrients">
      {block(t("recipes.per_100g"), recipe.per_100g, "per-100g")}
      {recipe.per_serving
        ? block(t("recipes.per_serving"), recipe.per_serving, "per-serving")
        : null}
    </div>
  );
}
