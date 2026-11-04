import { NutriScoreChip } from "@/components/ui/NutriScoreChip";

/**
 * Nutri-Score as the API computed it: a square letter tile (not a pill, so it
 * never reads as a verdict status), labelled "calculated by SmartNutri" only
 * when a grade is shown.
 */
export function GradeChip({
  grade,
  reason = null,
}: {
  grade: string | null;
  /** The API's `nutriscore.reason` (a supplement is never graded). */
  reason?: string | null;
}) {
  return <NutriScoreChip grade={grade} reason={reason} />;
}
