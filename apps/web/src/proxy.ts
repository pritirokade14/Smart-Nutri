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
  "result",
  "members",
  "history",
  "meals",
  "product",
  "settings",
]);

type Decision = { protected: boolean; locale: string; path: string };

// Next and next-intl route on the DECODED path (/en/%68ome serves /en/home),
// so the gate must decide on the decoded path too. Undecodable = protected.
function classify(pathname: string): Decision {
  let path: string;
  try {
    path = decodeURI(pathname);
  } catch {
    return { protected: true, locale: routing.defaultLocale, path: "" };
  }
  const [, first, segment] = path.split("/");
  const known = (routing.locales as readonly string[]).includes(first ?? "");
  return {
    protected: known && segment !== undefined && PROTECTED.has(segment),
    locale: known ? (first as string) : routing.defaultLocale,
    path,
  };
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
  const decision = classify(req.nextUrl.pathname);
  if (!decision.protected) return withHeaders(res, headers);

  // 2. session refresh (also for next-intl redirects: the target is re-gated,
  //    but never trust that on a protected path)
  const { signedIn } = await updateSession(intlReq, res);

  // 3. protect
  if (!signedIn) {
    const url = req.nextUrl.clone();
    url.pathname = `/${decision.locale}/sign-in`;
    url.search = "";
    if (decision.path) url.searchParams.set("next", decision.path);
    const redirect = NextResponse.redirect(url, 302);
    for (const c of res.cookies.getAll()) redirect.cookies.set(c);
    return withHeaders(redirect, headers);
  }
  return withHeaders(res, headers);
}

export const config = {
  matcher: ["/((?!api|auth(?:/|$)|_next|.*\\..*).*)"],
};
