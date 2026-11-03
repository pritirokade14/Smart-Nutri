import { NextIntlClientProvider } from "next-intl";
import {
  getMessages,
  getTranslations,
  setRequestLocale,
} from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { ErrorState } from "@/components/ui/ErrorState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { CompareView } from "@/features/product/components/CompareView";
import { compareRef, hasSide } from "@/features/product/lib/compareRefs";
import { resultMessages } from "@/i18n/client-messages";

type SearchParams = Record<string, string | string[] | undefined>;

// /compare?a=<id>|a_barcode=<code>[&b=<id>|b_barcode=<code>]. Query values
// are only UUIDs or barcodes (the analytics before_send drops query strings).
// The member statuses need the `status` namespace, so the view gets the
// result catalogue.
export default async function ComparePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<SearchParams>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const sp = await searchParams;
  const a = compareRef(sp, "a");
  const b = compareRef(sp, "b");
  if (!a || (hasSide(sp, "b") && !b)) {
    const t = await getTranslations({ locale });
    return (
      <main className={pageClass}>
        <SectionHeader as="h1" title={t("compare.title")} />
        <ErrorState
          message={t("error.invalid_product_ref")}
          retryHref={`/${locale}/search`}
          retryLabel={t("search.title")}
        />
      </main>
    );
  }
  const messages = resultMessages(await getMessages({ locale }));
  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <CompareView a={a} b={b} />
    </NextIntlClientProvider>
  );
}
