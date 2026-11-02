import { NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { ResultView } from "@/features/analysis/components/ResultView";
import { resultMessages } from "@/i18n/client-messages";

// Logged-in result page (the proxy and the (app) layout require a session).
// The root layout strips the verdict namespaces from the client catalogue, so
// the client result view gets its own provider with exactly those added back.
export default async function ResultPage({
  params,
}: {
  params: Promise<{ locale: string; barcode: string }>;
}) {
  const { locale, barcode } = await params;
  setRequestLocale(locale);
  const messages = resultMessages(await getMessages({ locale }));
  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <ResultView barcode={barcode} />
    </NextIntlClientProvider>
  );
}
