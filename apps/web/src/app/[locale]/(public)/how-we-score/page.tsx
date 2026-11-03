import type { Metadata } from "next";
import { hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { ErrorState } from "@/components/ui/ErrorState";
import { getMethodology } from "@/features/methodology/api/getMethodology";
import { MethodologyView } from "@/features/methodology/components/MethodologyView";
import { routing } from "@/i18n/routing";
import { localeAlternates, metadataBase } from "@/lib/seo";

type Params = Promise<{ locale: string }>;

// The API data is cached for an hour (getMethodology); the page itself is
// rendered per request because the root layout needs the CSP nonce.
export const revalidate = 3600;

export function generateStaticParams(): { locale: "en" | "hi" | "mr" }[] {
  return routing.locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale });
  return {
    metadataBase: metadataBase(),
    title: t("methodology.title"),
    description: t("methodology.meta_description"),
    alternates: localeAlternates(locale, (l) => `/${l}/how-we-score`),
  };
}

/** Public "How we score" (F12): no session, no client data hooks. */
export default async function HowWeScorePage({ params }: { params: Params }) {
  const { locale } = await params;
  setRequestLocale(locale);
  const language = hasLocale(routing.locales, locale)
    ? locale
    : routing.defaultLocale;
  const result = await getMethodology(language);
  const t = await getTranslations({ locale });
  return (
    <main className={`${pageClass} max-w-3xl px-4 py-8 md:px-6 md:py-12`}>
      {result.kind === "ok" ? (
        <MethodologyView data={result.data} />
      ) : (
        <>
          <h1 className="text-2xl font-bold text-text-primary sm:text-3xl">
            {t("methodology.title")}
          </h1>
          <ErrorState
            message={t("methodology.unavailable")}
            retryHref={`/${locale}/how-we-score`}
          />
        </>
      )}
    </main>
  );
}
