"use client";

import { useTranslations } from "next-intl";
import { BandBadge } from "@/features/history/components/BandBadge";
import { formatAmount, shownTotal } from "@/features/history/lib/summary";
import type { Summary } from "@/features/meals/api/meals";
import type { MemberOut } from "@/features/members/api/members";

// Latin digits in every locale, up to 2 decimals (the g per kg basis).
const TWO_DP = new Intl.NumberFormat("en", { maximumFractionDigits: 2 });

/**
 * The basis of the API's daily protein guide, for the guide sentence:
 * `limits.protein_g_per_kg` exactly as the API sent it (the YAML g per kg the
 * target was computed with). Null when the API sends none: then no basis is
 * shown. Never derived on the client.
 */
export function perKgBasis(perKg: number | null | undefined): string | null {
  return typeof perKg === "number" && perKg > 0 ? TWO_DP.format(perKg) : null;
}

/**
 * Today's protein for one member (GET /v1/meals/summary, period=day), as the
 * API sent it: the total against `limits.protein_target_g` and
 * `protein_left_g`, worded as a guide (decision 5; never "you need"). No
 * target (children, unknown age, no weight) shows the neutral note and a
 * link to the member form. An unknown total is the grey "Not enough data",
 * never green, with no progress bar. Calories are information only.
 */
export function ProteinProgress({
  summary,
  member,
  locale,
  notes = false,
}: {
  summary: Summary;
  member?: MemberOut;
  locale: string;
  /** The Protein page adds the kidney note. */
  notes?: boolean;
}) {
  const t = useTranslations();
  const incomplete = summary.incomplete?.protein_g === true;
  const total = shownTotal(summary.totals?.protein_g, incomplete);
  const target = summary.limits?.protein_target_g ?? null;
  const left = summary.protein_left_g;
  const kcal = shownTotal(
    summary.totals?.energy_kcal,
    summary.incomplete?.energy_kcal === true,
  );
  const perKg = perKgBasis(summary.limits?.protein_g_per_kg);
  // The API nulls what the member hid; show the hidden note, never "not enough data".
  const macrosHidden = summary.numbers_hidden?.macros === true;
  const paused = summary.limits?.protein_target_status === "paused_pregnancy";
  const guideKey = {
    lean_mass: "protein.guide_lean",
    adjusted_weight: "protein.guide_adjusted",
    actual_weight: "protein.guide",
  }[summary.limits?.protein_basis ?? "actual_weight"];
  const pct =
    total !== null && target !== null && target > 0
      ? Math.min(100, Math.round((total / target) * 100))
      : null;
  if (macrosHidden)
    return (
      <div className="space-y-3" data-testid="protein-progress">
        <p className="text-md font-semibold text-text-primary">
          {t("summary.nutrient.protein_g")}
        </p>
        <p className="text-sm text-text-secondary">
          {t("diary.hidden_numbers")}
        </p>
        {kcal !== null ? (
          <p className="text-md text-text-primary">
            {t("summary.kcal_total", { total: formatAmount(kcal) })}
          </p>
        ) : null}
        <p className="text-sm text-text-secondary">{t("diary.disclaimer")}</p>
      </div>
    );
  return (
    <div className="space-y-3" data-testid="protein-progress">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-md font-semibold text-text-primary">
          {total === null
            ? t("summary.nutrient.protein_g")
            : target !== null
              ? t("protein.progress", {
                  total: formatAmount(total),
                  target: formatAmount(target),
                })
              : t("summary.total_g", { total: formatAmount(total) })}
        </p>
        {total === null ? <BandBadge band="unknown" /> : null}
      </div>
      {pct !== null && target !== null && total !== null ? (
        // Decorative: the sentence above carries the numbers.
        <div
          aria-hidden="true"
          data-testid="protein-bar"
          className="h-2 w-full overflow-hidden rounded-full bg-surface-muted"
        >
          <div
            className="h-full rounded-full bg-brand-primary"
            style={{ width: `${pct}%` }}
          />
        </div>
      ) : null}
      {typeof left === "number" ? (
        <p className="text-md text-text-primary">
          {t("protein.left_today", { left: formatAmount(left) })}
        </p>
      ) : null}
      {incomplete ? (
        <p className="text-sm text-text-secondary">{t("summary.incomplete")}</p>
      ) : null}
      {target !== null && perKg !== null ? (
        <p className="text-sm text-text-secondary">
          {t(guideKey, { target: formatAmount(target), per_kg: perKg })}
        </p>
      ) : null}
      {target === null ? (
        <div className="space-y-1">
          <p className="text-sm text-text-secondary">
            {paused ? t("targets.pregnancy.paused") : t("protein.no_target")}
          </p>
          {member && !paused ? (
            <a
              href={`/${locale}/members/${member.id}`}
              className="inline-flex min-h-11 items-center text-md font-semibold text-brand-primary underline-offset-4 hover:underline"
            >
              {t("members.edit")}
            </a>
          ) : null}
        </div>
      ) : null}
      {kcal !== null ? (
        <p className="text-md text-text-primary">
          {t("summary.kcal_total", { total: formatAmount(kcal) })}
        </p>
      ) : null}
      <p className="text-sm text-text-secondary">{t("summary.kcal_info")}</p>
      {notes ? (
        <p className="text-sm text-text-secondary">
          {t("protein.kidney_note")}
        </p>
      ) : null}
    </div>
  );
}
