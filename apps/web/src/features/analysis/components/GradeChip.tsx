import { NutriScoreChip } from "@/components/ui/NutriScoreChip";

/**
 * Nutri-Score as the API computed it: a square letter tile (not a pill, so it
 * never reads as a verdict status), labelled "calculated by SmartNutri" only
 * when a grade is shown.
 */
export function GradeChip({ grade }: { grade: string | null }) {
  return <NutriScoreChip grade={grade} />;
}
