"use client";

import { useTranslations } from "next-intl";
import { parseWarning } from "../lib/warnings";

// Shown prominently (role=alert): the whole draft may be misread.
const PROMINENT = new Set(["low_confidence", "unreadable_field"]);

/**
 * One draft warning: `warning.<code>`, plus the field's label for `code:path`
 * warnings. Caution-coloured, never a verdict colour and never green.
 */
export function WarningBanner({ warning }: { warning: string }) {
  const t = useTranslations();
  const w = parseWarning(warning);
  const key = `warning.${w.code}`;
  // An unknown code still tells the user to check the pack.
  const message = t.has(key) ? t(key) : t("confirm.subtitle");
  const fieldKey =
    w.field === "serving_size_g"
      ? "confirm.serving_size"
      : w.field
        ? `confirm.field.${w.field}`
        : null;
  const fieldLabel = fieldKey && t.has(fieldKey) ? t(fieldKey) : null;
  const prominent = PROMINENT.has(w.code);
  return (
    <div
      data-testid={`warning-${warning}`}
      role={prominent ? "alert" : "note"}
      className={`rounded-(--radius-md) border-2 border-(--color-verdict-caution) p-(--spacing-3) text-(length:--text-md) ${prominent ? "font-semibold" : ""}`}
    >
      {fieldLabel ? (
        <p className="font-semibold text-(length:--text-sm)">{fieldLabel}</p>
      ) : null}
      <p>{message}</p>
    </div>
  );
}
