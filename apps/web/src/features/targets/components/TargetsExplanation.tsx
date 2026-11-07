"use client";

import { useLocale, useTranslations } from "next-intl";
import type { TargetsOut } from "../api/targets";
import { formatInt, formatRate, formatWeight } from "../lib/format";

const PROTEIN_KEY = {
  lean_mass: "targets.how.protein_lean",
  adjusted_weight: "targets.how.protein_adjusted",
  actual_weight: "targets.how.protein",
} as const;

/**
 * "How we got this": the API's explanation as lines. A value the API nulled
 * (hidden numbers) has no line, so nothing leaks. The sources link to the
 * methodology page.
 */
export function TargetsExplanation({ targets }: { targets: TargetsOut }) {
  const t = useTranslations();
  const locale = useLocale();
  const e = targets.explanation;
  if (!e) return null;
  const lines: { id: string; text: string }[] = [];
  if (e.bmr_kcal != null)
    lines.push({
      id: "bmr",
      text: t("targets.how.bmr", { value: formatInt(e.bmr_kcal) }),
    });
  if (e.activity_factor != null)
    lines.push({
      id: "activity",
      text: t("targets.how.activity", { value: formatRate(e.activity_factor) }),
    });
  if (e.maintenance_kcal != null)
    lines.push({
      id: "maintenance",
      text: t("targets.how.maintenance", {
        value: formatInt(e.maintenance_kcal),
      }),
    });
  if (e.adjustment_kcal != null)
    lines.push({
      id: "adjustment",
      text: t("targets.how.adjustment", {
        value: formatInt(e.adjustment_kcal),
      }),
    });
  if (e.protein_g_per_kg != null && e.protein_reference_weight_kg != null)
    lines.push({
      id: "protein",
      text: t(PROTEIN_KEY[e.protein_basis], {
        per_kg: formatRate(e.protein_g_per_kg),
        weight: formatWeight(e.protein_reference_weight_kg),
      }),
    });
  if (e.floor_kcal != null)
    lines.push({
      id: "floor",
      text: t("targets.how.floor", { value: formatInt(e.floor_kcal) }),
    });
  return (
    <details
      className="rounded-md border border-border-default p-3"
      data-testid="targets-explanation"
    >
      <summary className="min-h-11 cursor-pointer text-md font-semibold text-text-primary">
        {t("targets.how.title")}
      </summary>
      <ul className="mt-2 space-y-1">
        {lines.map((l) => (
          <li key={l.id} data-line={l.id} className="text-sm text-text-primary">
            {l.text}
          </li>
        ))}
      </ul>
      <a
        href={`/${locale}/how-we-score`}
        className="mt-2 inline-flex min-h-11 items-center text-md font-semibold text-brand-primary underline-offset-4 hover:underline"
      >
        {t("targets.how.sources")}
      </a>
    </details>
  );
}
