"use client";

import { useTranslations } from "next-intl";

/**
 * The credit line(s) for a food or entry: each attribution key the API sends
 * (attribution.usda_fdc, attribution.off, attribution.smartnutri_recipe)
 * through the catalogue. Unknown keys are skipped, never shown raw.
 */
export function SourceCredit({
  keys,
  className,
}: {
  keys: readonly string[] | null | undefined;
  className?: string;
}) {
  const t = useTranslations();
  const known = [...new Set(keys ?? [])].filter((k) => t.has(k));
  if (known.length === 0) return null;
  return (
    <span
      data-testid="source-credit"
      className={className ?? "block space-y-0.5 text-xs text-text-secondary"}
    >
      {known.map((k) => (
        <span key={k} className="block">
          {t(k)}
        </span>
      ))}
    </span>
  );
}
