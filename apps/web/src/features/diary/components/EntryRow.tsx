"use client";

import { useTranslations } from "next-intl";
import { chipClass } from "@/components/ui/Chip";
import { formatAmount } from "@/features/history/lib/summary";
import type { MealOut } from "../api/diary";

/**
 * One logged item. A quick add has no typed name by default ("Quick add") and
 * a badge. kcal shows unless null (hidden or unknown), and an entry with an
 * unknown nutrient carries the grey incomplete marker. Never a 0 for unknown.
 */
export function EntryRow({
  entry,
  onEdit,
}: {
  entry: MealOut;
  onEdit: (entry: MealOut) => void;
}) {
  const t = useTranslations();
  const quick = entry.source_kind === "quick_add";
  const name =
    quick && entry.product_name.trim() === ""
      ? t("diary.quick_add_name")
      : entry.product_name;
  const kcal = entry.nutrients.energy_kcal;
  return (
    <li data-testid="entry-row">
      <button
        type="button"
        onClick={() => onEdit(entry)}
        aria-label={`${t("diary.edit")}: ${name}`}
        className="flex min-h-11 w-full cursor-pointer flex-wrap items-center justify-between gap-2 px-4 py-3 text-left hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-brand-primary sm:px-5"
      >
        <span className="min-w-0 space-y-0.5">
          <span className="block text-md font-semibold break-words text-text-primary">
            {name}
          </span>
          <span className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-text-secondary">
            {quick ? (
              <span className={chipClass} data-testid="entry-quick-badge">
                {t("diary.quick_badge")}
              </span>
            ) : null}
            {entry.grams != null ? (
              <span data-testid="entry-portion" data-allow-digits>
                {t("diary.grams_line", { grams: formatAmount(entry.grams) })}
              </span>
            ) : null}
          </span>
        </span>
        <span className="flex flex-wrap items-center gap-2 text-md text-text-primary">
          {kcal !== null ? (
            <span data-testid="entry-kcal">
              {t("targets.kcal_value", { value: formatAmount(kcal) })}
            </span>
          ) : null}
          {entry.incomplete.length > 0 ? (
            <span className={chipClass} data-testid="entry-incomplete">
              {t("diary.incomplete")}
            </span>
          ) : null}
          {entry.grade ? (
            <span className={chipClass}>
              {t("result.grade", { grade: entry.grade })}
            </span>
          ) : null}
        </span>
      </button>
    </li>
  );
}
