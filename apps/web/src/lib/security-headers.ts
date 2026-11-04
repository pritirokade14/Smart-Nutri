function origin(url: string | undefined): string | null {
  if (!url) return null;
  try {
    return new URL(url).origin;
  } catch {
    return null;
  }
}

export function securityHeaders(nonce: string): Record<string, string> {
  const isDev = process.env.NODE_ENV === "development";
  const connect = [
    "'self'",
    origin(process.env.NEXT_PUBLIC_API_BASE_URL),
    origin(process.env.NEXT_PUBLIC_SUPABASE_URL),
    "https://*.sentry.io",
    "https://*.posthog.com",
  ].filter((v): v is string => Boolean(v));

  const csp = [
    "default-src 'self'",
    // 'unsafe-eval' is needed only by React/Next dev tooling (HMR, stack rebuild).
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isDev ? " 'unsafe-eval'" : ""}`,
    // Nonce-only styles: Next injects its <style> tags with the request nonce.
    `style-src 'self' 'nonce-${nonce}'`,
    `connect-src ${connect.join(" ")}`,
    "img-src 'self' data: blob: https://images.openfoodfacts.org",
    // Voice answers (F10) arrive inline and play from Blob URLs; nothing is
    // fetched from storage (ADR 0020).
    "media-src 'self' blob:",
    "font-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ");

  return {
    ...(process.env.NODE_ENV === "production"
      ? { "Strict-Transport-Security": "max-age=63072000; includeSubDomains" }
      : {}),
    "Content-Security-Policy": csp,
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(self), microphone=(self)",
  };
}
