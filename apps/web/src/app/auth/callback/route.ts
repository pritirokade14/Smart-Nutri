import { NextResponse } from "next/server";
import { routing } from "@/i18n/routing";
import { safeNext } from "@/lib/auth/safe-next";
import { createSupabaseServerClient } from "@/lib/supabase/server";

function localeOf(path: string | undefined): string | undefined {
  const first = path?.split("/")[1];
  return (routing.locales as readonly string[]).includes(first ?? "")
    ? first
    : undefined;
}

function cookieLocale(request: Request): string | undefined {
  const m = /(?:^|;\s*)NEXT_LOCALE=([^;]+)/.exec(
    request.headers.get("cookie") ?? "",
  );
  return localeOf(`/${m?.[1] ?? ""}`);
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  // Behind Cloud Run request.url is the bind address (0.0.0.0:8080): use the
  // public site URL. The request origin is only a dev/test fallback.
  const origin = process.env.NEXT_PUBLIC_SITE_URL
    ? new URL(process.env.NEXT_PUBLIC_SITE_URL).origin
    : url.origin;
  const fallbackLocale = cookieLocale(request) ?? routing.defaultLocale;
  const next = safeNext(
    url.searchParams.get("next"),
    `/${fallbackLocale}/home`,
  );
  const locale = localeOf(next) ?? fallbackLocale;
  const code = url.searchParams.get("code");

  if (code) {
    const supabase = await createSupabaseServerClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) return NextResponse.redirect(`${origin}${next}`);
  }
  return NextResponse.redirect(`${origin}/${locale}/sign-in?error=callback`);
}
