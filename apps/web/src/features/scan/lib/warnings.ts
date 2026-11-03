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
]);

/** Fields to highlight on the confirm screen, from the draft's warnings. */
export function highlightedFields(warnings: readonly string[]): Set<string> {
  const out = new Set<string>();
  for (const w of warnings) {
    const p = parseWarning(w);
    if (FIELD_CODES.has(p.code) && p.field) out.add(p.field);
  }
  return out;
}

export function hasWarning(warnings: readonly string[], code: string): boolean {
  return warnings.some((w) => parseWarning(w).code === code);
}

/** Ruling R19: any `unit_unconfirmed:*.sodium_mg`, on either printed column. */
export function sodiumUnitUnconfirmed(warnings: readonly string[]): boolean {
  return warnings.some((w) => {
    const p = parseWarning(w);
    return p.code === "unit_unconfirmed" && p.field === "sodium_mg";
  });
}
