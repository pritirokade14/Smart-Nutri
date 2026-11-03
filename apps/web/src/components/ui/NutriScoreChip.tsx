import { useTranslations } from "next-intl";
import { cn } from "@/lib/cn";

// Grade tile colours from the shared tokens, with a fixed on-colour per grade
// (not swapped in dark mode). Literal class names so Tailwind generates them.
const GRADE_CLASS: Record<string, string> = {
  A: "bg-grade-a text-grade-on-a",
  B: "bg-grade-b text-grade-on-b",
  C: "bg-grade-c text-grade-on-c",
  D: "bg-grade-d text-grade-on-d",
  E: "bg-grade-e text-grade-on-e",
};

/**
 * The Nutri-Score as the API computed it: a square letter tile (not a pill,
 * so it never reads as a member's status), always labelled "calculated by
 * SmartNutri". No grade: the insufficient-data line instead.
 */
export function NutriScoreChip({
  grade,
  showGradeLabel = false,
  creditWithoutGrade = false,
  className,
}: {
  grade: string | null;
  /** Also print "Nutri-Score X" next to the tile. */
  showGradeLabel?: boolean;
  /** Keep the "calculated by SmartNutri" line even with no grade (public page). */
  creditWithoutGrade?: boolean;
  className?: string;
}) {
  const t = useTranslations();
  const cls = grade ? GRADE_CLASS[grade] : undefined;
  if (!grade || !cls) {
    return (
      <div
        className={cn(
          "space-y-1 rounded-md bg-surface-muted px-3 py-2 text-sm text-text-secondary",
          className,
        )}
      >
        <p>{t("nutriscore.insufficient_data")}</p>
        {creditWithoutGrade ? <p>{t("nutriscore.calculated_by")}</p> : null}
      </div>
    );
  }
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <span
        data-testid="grade-tile"
        role="img"
        aria-label={t("result.grade", { grade })}
        className={cn(
          "flex h-12 w-12 shrink-0 items-center justify-center rounded-md text-xl font-bold shadow-sm",
          cls,
        )}
      >
        {grade}
      </span>
      <div className="min-w-0">
        {showGradeLabel ? (
          <p className="text-md font-semibold text-text-primary">
            {t("result.grade", { grade })}
          </p>
        ) : null}
        <p className="text-sm text-text-secondary">
          {t("nutriscore.calculated_by")}
        </p>
      </div>
    </div>
  );
}
