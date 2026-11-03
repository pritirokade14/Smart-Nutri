import type { MetadataRoute } from "next";
import { routing } from "@/i18n/routing";
import { metadataBase } from "@/lib/seo";

// The fixed public pages, in every locale with hreflang alternates. Product
// pages (/p/<barcode>) are not listed: there is no public product index yet.
const PAGES = ["", "/how-we-score", "/privacy", "/terms"] as const;

export default function sitemap(): MetadataRoute.Sitemap {
  const base = metadataBase();
  if (!base) return [];
  const url = (locale: string, page: string) =>
    new URL(`/${locale}${page}`, base).toString().replace(/\/$/, "");
  return PAGES.flatMap((page) =>
    routing.locales.map((locale) => ({
      url: url(locale, page),
      alternates: {
        languages: Object.fromEntries(
          routing.locales.map((l) => [l, url(l, page)]),
        ),
      },
    })),
  );
}
