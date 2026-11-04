"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { NutriScoreChip } from "@/components/ui/NutriScoreChip";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { VerdictBadge } from "@/components/ui/VerdictBadge";
import { OffAttribution } from "@/features/analysis/components/OffAttribution";
import { formatAmount } from "@/features/history/lib/summary";
import { QueryBody } from "@/features/home/components/cards/CardShell";
import type { MealOut } from "@/features/meals/api/meals";
import { todayIst } from "@/features/meals/api/meals";
import { useMealsForDay } from "@/features/meals/hooks/useMeals";
import { type ProductRef, productHref } from "@/features/product/api/products";
import { SearchBox } from "@/features/product/components/SearchBox";
import { useAlternatives } from "@/features/product/hooks/useProducts";

const refOf = (m: MealOut): ProductRef | null =>
  m.product_id
    ? { productId: m.product_id }
    : m.barcode
      ? { barcode: m.barcode }
      : null;

/** Higher-protein options for one logged item (sort=protein, this member). */
function Options({
  source,
  memberId,
}: {
  source: ProductRef;
  memberId: string;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const query = useAlternatives(source, memberId, "protein");
  return (
    <QueryBody
      query={query}
      render={(data) => {
        // The API never returns avoid for the member; this is only a guard.
        const items = data.items.filter((i) => i.member_status !== "avoid");
        if (items.length === 0)
          return (
            <p className="text-sm text-text-secondary">
              {data.reason !== "ok" &&
              data.reason !== "no_better_found" &&
              t.has(`alternatives.reason.${data.reason}`)
                ? t(`alternatives.reason.${data.reason}`)
                : t("protein.swaps_empty")}
            </p>
          );
        return (
          <>
            <ul className="space-y-2">
              {items.map((i) => {
                const href = productHref(locale, i);
                return (
                  <li
                    key={i.barcode ?? i.product_id ?? i.name}
                    data-testid="protein-swap"
                    className="flex flex-wrap items-center justify-between gap-3 rounded-md bg-surface-muted p-3"
                  >
                    <div className="min-w-0 space-y-1">
                      {href ? (
                        <a
                          href={href}
                          className="text-md font-semibold break-words text-text-primary hover:underline"
                        >
                          {i.name}
                        </a>
                      ) : (
                        <p className="text-md font-semibold break-words text-text-primary">
                          {i.name}
                        </p>
                      )}
                      {typeof i.protein_per_100kcal === "number" ? (
                        <p className="flex gap-1 text-sm text-text-secondary">
                          <span>{t("protein.per_100kcal")}</span>
                          <span className="font-semibold text-text-primary">
                            {t("summary.total_g", {
                              total: formatAmount(i.protein_per_100kcal),
                            })}
                          </span>
                        </p>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-2">
                      {i.member_status ? (
                        <VerdictBadge status={i.member_status} />
                      ) : null}
                      <NutriScoreChip grade={i.grade} />
                    </div>
                  </li>
                );
              })}
            </ul>
            {items.some((i) => i.attribution != null) ? (
              <OffAttribution barcode={null} />
            ) : null}
          </>
        );
      }}
    />
  );
}

/**
 * The protein guide's swaps (decision 6b, part 4): today's logged items for
 * the member, each with "Higher-protein options" from the API, and a
 * higher-protein product search. The API never suggests a product rated
 * `avoid` for the member, a supplement, or a worse Nutri-Score.
 */
export function ProteinSwaps({ memberId }: { memberId: string }) {
  const t = useTranslations();
  const meals = useMealsForDay(memberId, todayIst());
  const [open, setOpen] = useState<string | null>(null);
  return (
    <section className="space-y-3" aria-labelledby="protein-swaps-title">
      <SectionHeader
        id="protein-swaps-title"
        title={t("protein.swaps_title")}
      />
      <Card className="space-y-3">
        <QueryBody
          query={meals}
          render={(list) =>
            list.length === 0 ? (
              <p className="text-md text-text-secondary">
                {t("history.empty")}
              </p>
            ) : (
              <ul className="divide-y divide-border-default">
                {list.map((m) => {
                  const ref = refOf(m);
                  return (
                    <li key={m.id} className="space-y-2 py-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <p className="text-md font-semibold text-text-primary">
                          {m.product_name}
                        </p>
                        {ref ? (
                          <Button
                            variant="outline"
                            size="sm"
                            aria-expanded={open === m.id}
                            onClick={() =>
                              setOpen((o) => (o === m.id ? null : m.id))
                            }
                          >
                            {t("protein.swaps_title")}
                          </Button>
                        ) : null}
                      </div>
                      {ref && open === m.id ? (
                        <Options source={ref} memberId={memberId} />
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )
          }
        />
      </Card>
      <Card>
        <SearchBox memberId={memberId} defaultSort="protein" />
      </Card>
    </section>
  );
}
