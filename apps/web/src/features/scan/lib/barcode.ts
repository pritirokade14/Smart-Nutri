// Same rule as the API: digits only after stripping spaces/hyphens,
// length 8/12/13/14, leading zeros kept.
export function normalizeBarcode(raw: string): string | null {
  const s = raw.replace(/[\s-]/g, "");
  return /^\d+$/.test(s) && [8, 12, 13, 14].includes(s.length) ? s : null;
}
