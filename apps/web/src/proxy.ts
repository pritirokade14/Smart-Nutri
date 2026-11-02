import { NextRequest, NextResponse } from "next/server";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";
import { securityHeaders } from "./lib/security-headers";
import { updateSession } from "./lib/supabase/middleware";

const intl = createIntlMiddleware(routing);

// Route segment group "(app)": login required.
export const PROTECTED_SEGMENT = "(app)";
const PROTECTED = new Set([
  "home",
  "scan",
  "members",
  "history",
  "meals",
  "product",
  "settings",
]);

function localeAndSegment(pathname: string): [string | undefined, string?] {
  const [, locale, segment] = pathname.split("/");
  return [locale, segment];
}

function withHeaders(res: NextResponse, h: Record<string, string>) {
  for (const [k, v] of Object.entries(h)) res.headers.set(k, v);
  return res;
}

export async function proxy(req: NextRequest): Promise<NextResponse> {
  const nonce = btoa(crypto.randomUUID());
  const headers = securityHeaders(nonce);

  // Next reads the nonce from the request's CSP header to stamp its inline scripts.
  const reqHeaders = new Headers(req.headers);
  reqHeaders.set("x-nonce", nonce);
  reqHeaders.set("content-security-policy", headers["Content-Security-Policy"]);
  const intlReq = new NextRequest(req, { headers: reqHeaders });

  // 1. locale
  const res = intl(intlReq) as NextResponse;
  if (res.status >= 300 && res.status < 400) return withHeaders(res, headers);

  // 2. session refresh
  const { signedIn } = await updateSession(intlReq, res);

  // 3. protect
  const { pathname } = req.nextUrl;
  const [locale, segment] = localeAndSegment(pathname);
  const isProtected =
    locale !== undefined &&
    (routing.locales as readonly string[]).includes(locale) &&
    segment !== undefined &&
    PROTECTED.has(segment);
  if (isProtected && !signedIn) {
    const url = req.nextUrl.clone();
    url.pathname = `/${locale}/sign-in`;
    url.search = "";
    url.searchParams.set("next", pathname);
    return withHeaders(NextResponse.redirect(url, 302), headers);
  }

  // 4. headers
  return withHeaders(res, headers);
}

export const config = {
  matcher: ["/((?!api|auth(?:/|$)|_next|.*\\..*).*)"],
};
