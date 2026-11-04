// Readers for the protein-guide parts of the untyped `report` object
// (AnalyzeOut.report and PublicProductOut.report). They only read what the
// API computed: no protein value is ever derived here, and a missing value
// stays null (never 0).

export type ProteinFactsOut = {
  per_100g: number | null;
  per_serving: number | null;
  per_100kcal: number | null;
  serving_size_g: number | null;
};

const num = (v: unknown): number | null =>
  typeof v === "number" && Number.isFinite(v) ? v : null;

export function readProtein(report: Record<string, unknown>): ProteinFactsOut {
  const p = (report.protein ?? {}) as Record<string, unknown>;
  return {
    per_100g: num(p.per_100g),
    per_serving: num(p.per_serving),
    per_100kcal: num(p.per_100kcal),
    serving_size_g: num(p.serving_size_g),
  };
}

/** `report.sweeteners` or `report.caffeine`: the ingredient terms found. */
export function readTerms(
  report: Record<string, unknown>,
  key: "sweeteners" | "caffeine",
): string[] {
  const v = report[key];
  return Array.isArray(v)
    ? v.filter((x): x is string => typeof x === "string" && x.trim() !== "")
    : [];
}

/** `report.nutriscore.reason` (e.g. "not_scored_supplement"), or null. */
export function readNutriscoreReason(
  report: Record<string, unknown>,
): string | null {
  const ns = report.nutriscore as { reason?: unknown } | null | undefined;
  return typeof ns?.reason === "string" ? ns.reason : null;
}

/** True when the report carries protein facts at all (newer API). */
export function hasProteinFacts(report: Record<string, unknown>): boolean {
  return typeof report.protein === "object" && report.protein !== null;
}
