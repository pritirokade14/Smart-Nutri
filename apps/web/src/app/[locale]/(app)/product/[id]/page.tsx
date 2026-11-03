import { NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { ResultView } from "@/features/analysis/components/ResultView";
import { resultMessages } from "@/i18n/client-messages";

// Logged-in result for a saved product (e.g. a confirmed label scan), by id.
// Same provider set-up as the barcode result page.
export default async function ProductResultPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  const messages = resultMessages(await getMessages({ locale }));
  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <ResultView productId={id} />
    </NextIntlClientProvider>
  );
}
