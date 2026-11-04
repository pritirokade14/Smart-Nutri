import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { hasLocale } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { ErrorState } from "@/components/ui/ErrorState";
import { loadPublicProduct } from "@/features/product/api/public-product";
import { PublicProduct } from "@/features/product/components/PublicProduct";
import { normalizeBarcode } from "@/features/scan/lib/barcode";
import { routing } from "@/i18n/routing";
import { localeAlternates, metadataBase } from "@/lib/seo";

type Params = Promise<{ locale: string; barcode: string }>;

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
    alternates: localeAlternates(locale, (l) => path(l, barcode)),
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
      <main className={`${pageClass} max-w-3xl px-4 py-8 md:py-12`}>
        <ErrorState
          message={t("scan.off_unavailable")}
          retryHref={path(locale, barcode)}
          retryLabel={t("scan.retry")}
        />
      </main>
    );
  }
  return <PublicProduct data={result.data} barcode={barcode} />;
}
