import { NextIntlClientProvider } from "next-intl";
import {
  getMessages,
  getTranslations,
  setRequestLocale,
} from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { SearchBox } from "@/features/product/components/SearchBox";
import { resultMessages } from "@/i18n/client-messages";

// Product search (ours, then Open Food Facts). The query stays in the page
// state, never in the URL (paths and queries are sent to analytics). The
// "Higher protein" order shows the member's status, so the box gets the
// result catalogue (status labels).
export default async function SearchPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
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
        <SearchBox label={t("search.placeholder")} />
      </NextIntlClientProvider>
    </main>
  );
}
