import type { Basis } from "./draftSchema";

export type ParsedWarning = {
  raw: string;
  /** i18n key suffix: `warning.<code>`. */
  code: string;
  /** Everything after the first ":", e.g. "per_100g.sodium_mg"; null if none. */
  path: string | null;
  /** The last path segment, e.g. "sodium_mg"; null if no path. */
  field: string | null;
  /** The printed column the path names, if any. */
  column: Basis | null;
};

/** "unit_unconfirmed:per_100g.sodium_mg" → code, path, field and column. */
export function parseWarning(raw: string): ParsedWarning {
  const i = raw.indexOf(":");
  if (i < 0) return { raw, code: raw, path: null, field: null, column: null };
  const code = raw.slice(0, i);
  const path = raw.slice(i + 1);
  const parts = path.split(".");
  const field = parts.at(-1) || null;
  const first = parts[0];
  const column =
    parts.length > 1 && (first === "per_100g" || first === "per_serving")
      ? first
      : null;
  return { raw, code, path, field, column };
}

/** Warnings that point at one value the user must look at. */
const FIELD_CODES = new Set([
  "implausible_value",
  "unreadable_field",
  "upper_bound",
  "unit_unconfirmed",
  // Label v2: a possible x10 / ÷10 slip on one printed cell, and a nutrient
  // whose per 100 g and per-serving values disagree.
  "decimal_shift",
  "column_mismatch",
]);

/** Label v2 warnings without a path that still name the fields to check. */
const IMPLIED_FIELDS: Readonly<Record<string, readonly string[]>> = {
  // Saturated + trans fat add up to more than total fat.
  fat_parts_mismatch: ["fat_g", "sat_fat_g"],
};

/** Fields to highlight on the confirm screen, from the draft's warnings. */
export function highlightedFields(warnings: readonly string[]): Set<string> {
  const out = new Set<string>();
  for (const w of warnings) {
    const p = parseWarning(w);
    if (FIELD_CODES.has(p.code) && p.field) out.add(p.field);
    for (const f of IMPLIED_FIELDS[p.code] ?? []) out.add(f);
  }
  return out;
}

/** The known reasons an image was too poor to read (422 image_quality_low). */
const IMAGE_REASONS = ["blur", "glare", "too_small"] as const;
export type ImageReason = (typeof IMAGE_REASONS)[number];

/** `details.reasons` of an image_quality_low error, known ones only, in order. */
export function imageQualityReasons(details: unknown): ImageReason[] {
  const r = (details as { reasons?: unknown } | null | undefined)?.reasons;
  if (!Array.isArray(r)) return [];
  return IMAGE_REASONS.filter((x) => r.includes(x));
}

// Warnings drive banners and highlights only. Which boxes, bases, pickers
// and columns to show come from `draft.confirm` (Ruling R21), never from here.
