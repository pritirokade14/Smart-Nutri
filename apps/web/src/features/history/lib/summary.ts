// Display helpers for the API's meal summaries. They never compute a total,
// limit or band: they only decide how to SHOW what the API sent, and they
// only ever move a value towards "Not enough data", never towards "fine".

export type Band = "ok" | "near" | "over" | "unknown";

const BANDS = new Set<string>(["ok", "near", "over", "unknown"]);

/** The band as the API sent it; anything unexpected is unknown (grey), never ok. */
export function bandOf(band: unknown): Band {
  return typeof band === "string" && BANDS.has(band)
    ? (band as Band)
    : "unknown";
}

/**
 * A total the UI may print, or null for "Not enough data".
 * - null or missing: unknown (Ruling M1 makes Totals nullable; never 0).
 * - 0 with the nutrient incomplete: nothing known was summed (the API before
 *   M1 sent 0.0 here), so it is unknown too.
 */
export function shownTotal(
  total: number | null | undefined,
  incomplete: boolean | undefined,
): number | null {
  if (typeof total !== "number" || !Number.isFinite(total)) return null;
  if (incomplete && total === 0) return null;
  return total;
}

/**
 * The band to show next to a total. A total we cannot show is never "within"
 * or "close to" a limit; an "over" from the API is always kept.
 */
export function shownBand(band: unknown, total: number | null): Band {
  const b = bandOf(band);
  if (total === null && (b === "ok" || b === "near")) return "unknown";
  return b;
}

// Same as Android's NumberFormat.decimalPattern('en') with 1 fraction digit:
// Latin digits in every locale (packages/i18n README, rule 4).
const ONE_DP = new Intl.NumberFormat("en", { maximumFractionDigits: 1 });

export function formatAmount(n: number): string {
  return ONE_DP.format(n);
}

/** Nutrients in display order: key in totals/incomplete, key in bands. */
export const NUTRIENTS = [
  { key: "sugars_g", band: "sugar_g", banded: true },
  { key: "salt_g", band: "salt_g", banded: true },
  { key: "protein_g", band: "protein_g", banded: false },
  { key: "energy_kcal", band: "kcal", banded: false },
] as const;

export type NutrientKey = (typeof NUTRIENTS)[number]["key"];
export type BandKey = (typeof NUTRIENTS)[number]["band"];

/** Reads a total that may be null or missing whatever the contract says. */
export function readTotal(
  totals: object | null | undefined,
  key: NutrientKey,
): number | null | undefined {
  const v = (totals as Record<string, unknown> | null | undefined)?.[key];
  return typeof v === "number" ? v : v === null ? null : undefined;
}

export function readFlag(
  flags: object | null | undefined,
  key: NutrientKey,
): boolean {
  return (flags as Record<string, unknown> | null | undefined)?.[key] === true;
}

export function readBand(
  bands: object | null | undefined,
  key: BandKey,
): unknown {
  return (bands as Record<string, unknown> | null | undefined)?.[key];
}

/** Short weekday and day for a YYYY-MM-DD date, in the UI locale (Latin digits). */
export function dayLabel(date: string, locale: string): string {
  return new Intl.DateTimeFormat(`${locale}-u-nu-latn`, {
    weekday: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${date}T00:00:00Z`));
}

/** A long date for headings, e.g. "Monday, 3 November". */
export function longDateLabel(date: string, locale: string): string {
  return new Intl.DateTimeFormat(`${locale}-u-nu-latn`, {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "UTC",
  }).format(new Date(`${date}T00:00:00Z`));
}
