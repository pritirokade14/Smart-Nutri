import { NextIntlClientProvider } from "next-intl";
import {
  getMessages,
  getTranslations,
  setRequestLocale,
} from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { SEARCH_MAX } from "@/features/product/api/products";
import { SearchBox } from "@/features/product/components/SearchBox";
import { resultMessages } from "@/i18n/client-messages";

// Product search (ours, then Open Food Facts). The query is read from ?q= (links that
// pass it) but we never write it to the URL (queries go to analytics). The
// "Higher protein" order shows the member's status, so the box gets the
// result catalogue (status labels).
export default async function SearchPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ q?: string | string[] }>;
}) {
  const { locale } = await params;
  const { q } = await searchParams;
  const initialQuery = (Array.isArray(q) ? q[0] : q) ?? "";
  setRequestLocale(locale);
  const t = await getTranslations({ locale });
  const messages = resultMessages(await getMessages({ locale }));
  return (
    <main className={pageClass}>
      <SectionHeader
        as="h1"
        title={t("search.title")}
        description={t("search.hint")}
      />
      <NextIntlClientProvider locale={locale} messages={messages}>
        <SearchBox
          label={t("search.placeholder")}
          initialQuery={initialQuery.slice(0, SEARCH_MAX)}
        />
      </NextIntlClientProvider>
    </main>
  );
}
