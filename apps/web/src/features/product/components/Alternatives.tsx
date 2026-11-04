"use client";

import { useLocale, useTranslations } from "next-intl";
import { useId, useState } from "react";
import { buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { chipClass } from "@/components/ui/Chip";
import { ErrorState } from "@/components/ui/ErrorState";
import { inputClass, labelClass } from "@/components/ui/field";
import { NutriScoreChip } from "@/components/ui/NutriScoreChip";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState } from "@/components/ui/Skeleton";
import { VerdictBadge } from "@/components/ui/VerdictBadge";
import { OffAttribution } from "@/features/analysis/components/OffAttribution";
import { formatAmount } from "@/features/history/lib/summary";
import type { LogMealMember } from "@/features/meals/components/LogMealDialog";
import { SortToggle } from "@/features/protein/components/SortToggle";
import type { ApiError } from "@/lib/api/errors";
import {
  type AlternativeOut,
  type AlternativesSort,
  compareHref,
  compareParams,
  type ProductRef,
  productHref,
} from "../api/products";
import { useAlternatives } from "../hooks/useProducts";

const HIGH_IN = new Set(["sugar", "fat", "sat_fat", "salt"]);
const REASONS = new Set([
  "no_category",
  "no_better_found",
  "source_ungraded",
  "source_supplement",
  "source_protein_unknown",
]);

/**
 * Healthier options (same Open Food Facts category, strictly better
 * Nutri-Score calculated by SmartNutri), in the API's order, with the rules
 * engine's status for the chosen member. An option that is `avoid` for that
 * member is never listed (Ruling M1: the API drops them; this is the client's
 * guard); with nothing left, the list says no better product was found.
 */
export function Alternatives({
  productRef,
  members,
}: {
  productRef: ProductRef;
  members: readonly LogMealMember[];
}) {
  const t = useTranslations();
  const locale = useLocale();
  const selectId = useId();
  const [memberId, setMemberId] = useState<string | null>(
    members[0]?.id ?? null,
  );
  const [sort, setSort] = useState<AlternativesSort>("grade");
  const query = useAlternatives(productRef, memberId, sort);
  const member = members.find((m) => m.id === memberId);
  const memberName = member
    ? member.name.trim() !== ""
      ? member.name
      : member.isPrimary
        ? t("result.you")
        : t(`share.relation.${member.relation ?? "other"}`)
    : null;
  const source = compareParams(
    "a",
    "productId" in productRef
      ? { product_id: productRef.productId, barcode: null }
      : { product_id: null, barcode: productRef.barcode },
  );

  const errorText = (e: ApiError) => {
    if (e.code === "off_unavailable") return t("scan.off_unavailable");
    return t.has(`error.${e.code}`)
      ? t(`error.${e.code}`)
      : t("error.internal_error");
  };

  let body: React.ReactNode;
  if (query.isPending) {
    body = <LoadingState label={t("common.loading")} lines={1} />;
  } else if (query.isError) {
    body = (
      <ErrorState
        message={errorText(query.error)}
        onRetry={() => query.refetch()}
        retrying={query.isFetching}
      />
    );
  } else {
    const items = query.data.items.filter(
      (i: AlternativeOut) => !(memberId && i.member_status === "avoid"),
    );
    if (items.length === 0) {
      const reason =
        query.data.reason !== "ok" && REASONS.has(query.data.reason)
          ? query.data.reason
          : "no_better_found";
      body = (
        <p
          data-testid="alternatives-empty"
          className="text-md text-text-secondary"
        >
          {sort === "protein" && reason === "no_better_found"
            ? t("protein.swaps_empty")
            : t(`alternatives.reason.${reason}`)}
        </p>
      );
    } else {
      body = (
        <>
          <ul className="space-y-3">
            {items.map((i) => {
              const href = productHref(locale, i);
              const target = compareParams("b", i);
              return (
                <Card
                  as="li"
                  key={i.barcode ?? i.product_id ?? i.name}
                  data-testid="alternative"
                  className="space-y-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      {href ? (
                        <a
                          href={href}
                          className="text-md font-semibold break-words text-text-primary underline-offset-4 hover:underline"
                        >
                          {i.name}
                        </a>
                      ) : (
                        <p className="text-md font-semibold break-words text-text-primary">
                          {i.name}
                        </p>
                      )}
                      {i.brand ? (
                        <p className="text-sm text-text-secondary">{i.brand}</p>
                      ) : null}
                      {typeof i.sugars_g === "number" ? (
                        <p className="text-sm text-text-secondary">
                          {t("alternatives.sugars", {
                            value: formatAmount(i.sugars_g),
                          })}
                        </p>
                      ) : null}
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
                    <NutriScoreChip grade={i.grade} />
                  </div>
                  {i.high_in.some((k) => HIGH_IN.has(k)) ? (
                    <ul className="flex flex-wrap gap-2">
                      {i.high_in
                        .filter((k) => HIGH_IN.has(k))
                        .map((k) => (
                          <li key={k} className={chipClass}>
                            {t(`high_in.${k}`)}
                          </li>
                        ))}
                    </ul>
                  ) : null}
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    {i.member_status && memberName ? (
                      <span className="flex items-center gap-2 text-sm text-text-secondary">
                        {t("alternatives.for_member", { name: memberName })}
                        <VerdictBadge status={i.member_status} />
                      </span>
                    ) : (
                      <span />
                    )}
                    {source && target ? (
                      <a
                        href={compareHref(locale, source, target)}
                        className={buttonClass({
                          variant: "outline",
                          size: "sm",
                        })}
                      >
                        {t("alternatives.compare")}
                      </a>
                    ) : null}
                  </div>
                </Card>
              );
            })}
          </ul>
          {items.some((i) => i.attribution != null) ? (
            <OffAttribution barcode={null} />
          ) : null}
        </>
      );
    }
  }

  return (
    <section
      data-testid="alternatives"
      aria-labelledby={`${selectId}-title`}
      className="space-y-3"
    >
      <SectionHeader
        id={`${selectId}-title`}
        title={t("alternatives.title")}
        description={t("alternatives.subtitle")}
      />
      {members.length > 1 ? (
        <div className="space-y-1">
          <label htmlFor={selectId} className={labelClass}>
            {t("history.member")}
          </label>
          <select
            id={selectId}
            value={memberId ?? ""}
            onChange={(e) => setMemberId(e.target.value || null)}
            className={inputClass}
          >
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name.trim() !== ""
                  ? m.name
                  : m.isPrimary
                    ? t("result.you")
                    : t(`share.relation.${m.relation ?? "other"}`)}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      <SortToggle
        options={[
          { value: "grade", label: t("alternatives.title") },
          { value: "protein", label: t("protein.sort_higher") },
        ]}
        value={sort}
        onChange={setSort}
      />
      {body}
    </section>
  );
}
