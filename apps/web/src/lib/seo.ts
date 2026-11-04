import type { Metadata } from "next";
import { routing } from "@/i18n/routing";

// Paths stay relative; Next resolves them against metadataBase (the site
// origin), so canonical and hreflang come out absolute when it is set.
export function metadataBase(): URL | undefined {
  try {
    const site = process.env.NEXT_PUBLIC_SITE_URL;
    return site ? new URL(site) : undefined;
  } catch {
    return undefined;
  }
}

/** Canonical plus one hreflang alternate per locale for a public path. */
export function localeAlternates(
  locale: string,
  pathFor: (locale: string) => string,
): Metadata["alternates"] {
  return {
    canonical: pathFor(locale),
    languages: Object.fromEntries(routing.locales.map((l) => [l, pathFor(l)])),
  };
}
