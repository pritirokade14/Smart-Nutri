import { useTranslations } from "next-intl";

// Grade token background with a readable text colour (bold and large, so the
// tile counts as large text for contrast).
const GRADE_CLASS: Record<string, string> = {
  A: "bg-(--color-grade-a) text-(--color-surface-default)",
  B: "bg-(--color-grade-b) text-(--color-text-primary)",
  C: "bg-(--color-grade-c) text-(--color-text-primary)",
  D: "bg-(--color-grade-d) text-(--color-text-primary)",
  E: "bg-(--color-grade-e) text-(--color-text-primary)",
};

/**
 * Nutri-Score as the API computed it: a square letter tile (not a pill, so it
 * never reads as a verdict status), labelled "calculated by SmartNutri" only
 * when a grade is shown.
 */
export function GradeChip({ grade }: { grade: string | null }) {
  const t = useTranslations();
  const cls = grade ? GRADE_CLASS[grade] : undefined;
  return (
    <section className="space-y-(--spacing-1)">
      {grade && cls ? (
        <div className="flex items-center gap-(--spacing-3)">
          <span
            data-testid="grade-tile"
            role="img"
            aria-label={t("result.grade", { grade })}
            className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-(--radius-sm) text-(length:--text-xl) font-bold ${cls}`}
          >
            {grade}
          </span>
          <p className="text-(length:--text-sm)">
            {t("nutriscore.calculated_by")}
          </p>
        </div>
      ) : (
        <p className="text-(length:--text-sm)">
          {t("nutriscore.insufficient_data")}
        </p>
      )}
    </section>
  );
}
