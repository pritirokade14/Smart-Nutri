const BASE = "http://safe.invalid";

function hasControlChars(v: string): boolean {
  for (let i = 0; i < v.length; i++) {
    const c = v.charCodeAt(i);
    if (c <= 0x1f || c === 0x7f) return true;
  }
  return false;
}

function isSafe(v: string): boolean {
  return (
    v.startsWith("/") &&
    !v.startsWith("//") &&
    !v.includes("\\") &&
    !hasControlChars(v)
  );
}

/**
 * Returns a normalised same-origin relative path for `next`, else `fallback`.
 * Normalising (dot segments, encoded dots) closes `/.//evil.com`-style tricks.
 */
export function safeNext(
  next: string | null | undefined,
  fallback: string,
): string {
  if (!next || typeof next !== "string") return fallback;
  let decoded: string;
  try {
    decoded = decodeURIComponent(next);
  } catch {
    return fallback;
  }
  if (!isSafe(next) || !isSafe(decoded)) return fallback;
  try {
    const u = new URL(next, BASE);
    if (u.origin !== BASE || u.pathname.startsWith("//")) return fallback;
    return u.pathname + u.search + u.hash;
  } catch {
    return fallback;
  }
}
