import type { MetadataRoute } from "next";
import { metadataBase } from "@/lib/seo";

// Public pages are crawlable; the signed-in app and the auth/API routes are
// not (they need a session and hold personal data). Locale-prefixed app
// routes use a wildcard segment.
const APP_ROUTES = [
  "home",
  "scan",
  "search",
  "compare",
  "family",
  "history",
  "diary",
  "members",
  "product",
  "result",
  "profile",
  "guide",
];

export default function robots(): MetadataRoute.Robots {
  const base = metadataBase();
  return {
    rules: {
      userAgent: "*",
      allow: ["/"],
      disallow: ["/api/", "/auth/", ...APP_ROUTES.map((r) => `/*/${r}`)],
    },
    sitemap: base ? new URL("/sitemap.xml", base).toString() : undefined,
  };
}
