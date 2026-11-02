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

/** Returns `next` only if it is a same-origin relative path, else `fallback`. */
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
    const base = "http://safe.invalid";
    if (new URL(next, base).origin !== base) return fallback;
  } catch {
    return fallback;
  }
  return next;
}
