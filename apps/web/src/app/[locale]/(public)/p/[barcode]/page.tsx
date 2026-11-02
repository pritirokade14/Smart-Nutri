import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { loadPublicProduct } from "@/features/product/api/public-product";
import { PublicProduct } from "@/features/product/components/PublicProduct";
import { normalizeBarcode } from "@/features/scan/lib/barcode";
import { routing } from "@/i18n/routing";

type Params = Promise<{ locale: string; barcode: string }>;

// Paths stay relative; Next resolves them against metadataBase (the site
// origin), so canonical and hreflang come out absolute when it is set.
function metadataBase(): URL | undefined {
  try {
    const site = process.env.NEXT_PUBLIC_SITE_URL;
    return site ? new URL(site) : undefined;
  } catch {
    return undefined;
  }
}
const path = (locale: string, barcode: string) => `/${locale}/p/${barcode}`;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { locale, barcode: raw } = await params;
  const barcode = normalizeBarcode(raw);
  if (!hasLocale(routing.locales, locale) || !barcode) return {};
  const t = await getTranslations({ locale });
  const result = await loadPublicProduct(barcode);
  if (result.kind !== "ok")
    return { metadataBase: metadataBase(), robots: { index: false } };
  const name = result.data.product.name ?? barcode;
  return {
    metadataBase: metadataBase(),
    title: t("product.meta_title", { name }),
    description: t("product.meta_description"),
    alternates: {
      canonical: path(locale, barcode),
      languages: Object.fromEntries(
        routing.locales.map((l) => [l, path(l, barcode)]),
      ),
    },
  };
}

export default async function PublicProductPage({
  params,
}: {
  params: Params;
}) {
  const { locale, barcode: raw } = await params;
  setRequestLocale(locale);
  const barcode = normalizeBarcode(raw);
  if (!barcode) notFound();
  const result = await loadPublicProduct(barcode);
  if (result.kind === "not_found") notFound();
  if (result.kind === "unavailable") {
    const t = await getTranslations({ locale });
    return (
      <main className="mx-auto max-w-xl space-y-(--spacing-4) p-(--spacing-4)">
        <p className="text-(length:--text-md)">{t("scan.off_unavailable")}</p>
        <a
          href={`/${locale}/p/${barcode}`}
          className="underline text-(length:--text-md)"
        >
          {t("scan.retry")}
        </a>
      </main>
    );
  }
  return <PublicProduct data={result.data} barcode={barcode} />;
}
