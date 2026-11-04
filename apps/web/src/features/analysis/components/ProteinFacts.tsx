import { useTranslations } from "next-intl";
import { Card } from "@/components/ui/Card";
import { chipClass } from "@/components/ui/Chip";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { formatAmount } from "@/features/history/lib/summary";
import { readProtein, readTerms } from "@/features/protein/lib/reportProtein";

const ROWS = ["per_serving", "per_100g", "per_100kcal"] as const;

/**
 * Protein per serving, per 100 g and per 100 kcal, and the sweeteners and
 * caffeine found in the ingredients, exactly as the API's report sent them
 * (decision 6b, parts 2 and 3). A missing value reads "Not on the label",
 * never 0. Information only: these never change a verdict. Generic product
 * facts, so the public product page shows them too.
 */
export function ProteinFacts({ report }: { report: Record<string, unknown> }) {
  const t = useTranslations();
  const protein = readProtein(report);
  const sweeteners = readTerms(report, "sweeteners");
  const caffeine = readTerms(report, "caffeine");
  const terms = (list: string[]) =>
    list.filter((x) => x !== "contains_sweeteners");
  return (
    <Card as="section" className="space-y-3" data-testid="protein-facts">
      <SectionHeader title={t("protein.title")} />
      <dl className="divide-y divide-border-default">
        {ROWS.map((k) => {
          const v = protein[k];
          return (
            <div
              key={k}
              data-testid={`protein-${k}`}
              className="flex items-baseline justify-between gap-4 py-2"
            >
              <dt className="text-md text-text-primary">{t(`protein.${k}`)}</dt>
              <dd
                className={
                  v === null
                    ? "text-sm text-text-secondary"
                    : "text-md font-semibold text-text-primary tabular-nums"
                }
              >
                {v === null
                  ? t("protein.not_on_label")
                  : t("summary.total_g", { total: formatAmount(v) })}
              </dd>
            </div>
          );
        })}
      </dl>
      {[
        ["report.sweeteners", sweeteners],
        ["report.caffeine", caffeine],
      ].map(([key, list]) =>
        (list as string[]).length > 0 ? (
          <div key={key as string} className="space-y-2">
            <p className="text-sm font-semibold text-text-secondary">
              {t(key as string)}
            </p>
            {terms(list as string[]).length > 0 ? (
              <ul className="flex flex-wrap gap-2">
                {terms(list as string[]).map((x) => (
                  <li key={x} className={chipClass}>
                    {x}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null,
      )}
    </Card>
  );
}
