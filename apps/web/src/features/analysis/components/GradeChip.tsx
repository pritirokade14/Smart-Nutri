import { useTranslations } from "next-intl";

// Grade token background with a readable text colour (bold, so the chip counts
// as large text for contrast).
const GRADE_CLASS: Record<string, string> = {
  A: "bg-(--color-grade-a) text-(--color-surface-default)",
  B: "bg-(--color-grade-b) text-(--color-text-primary)",
  C: "bg-(--color-grade-c) text-(--color-text-primary)",
  D: "bg-(--color-grade-d) text-(--color-text-primary)",
  E: "bg-(--color-grade-e) text-(--color-text-primary)",
};

/** Nutri-Score as the API computed it, labelled "calculated by SmartNutri". */
export function GradeChip({ grade }: { grade: string | null }) {
  const t = useTranslations();
  const cls = grade ? GRADE_CLASS[grade] : undefined;
  return (
    <section className="space-y-(--spacing-1)">
      {grade && cls ? (
        <p
          className={`inline-block rounded-(--radius-md) px-(--spacing-3) py-(--spacing-1) text-(length:--text-lg) font-semibold ${cls}`}
        >
          {t("result.grade", { grade })}
        </p>
      ) : (
        <p className="text-(length:--text-sm)">
          {t("nutriscore.insufficient_data")}
        </p>
      )}
      <p className="text-(length:--text-sm)">{t("nutriscore.calculated_by")}</p>
    </section>
  );
}
