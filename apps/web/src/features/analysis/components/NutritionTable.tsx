import { useTranslations } from "next-intl";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatAmount, NUTRITION_ROWS, type NutrientsOut } from "../lib/report";

/**
 * "Nutrition per 100 g/ml": product.per_100g as the API sent it. A value the
 * label does not show says so ("Not on the label") and is never shown as 0.
 */
export function NutritionTable({ per100g }: { per100g: NutrientsOut }) {
  const t = useTranslations();
  return (
    <Card as="section" className="space-y-3" data-testid="nutrition-table">
      <SectionHeader title={t("result.nutrition_title")} />
      <dl className="divide-y divide-border-default">
        {NUTRITION_ROWS.map((k) => {
          const value = formatAmount(per100g[k]);
          return (
            <div
              key={k}
              data-nutrient={k}
              className="flex items-baseline justify-between gap-4 py-2"
            >
              <dt className="text-md text-text-primary">
                {t(`confirm.field.${k}`)}
              </dt>
              <dd
                className={
                  value === null
                    ? "text-sm text-text-secondary"
                    : "text-md font-semibold text-text-primary tabular-nums"
                }
              >
                {value ?? t("result.not_on_label")}
              </dd>
            </div>
          );
        })}
      </dl>
    </Card>
  );
}
