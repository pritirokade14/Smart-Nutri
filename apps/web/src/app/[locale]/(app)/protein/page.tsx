import { NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { ProteinScreen } from "@/features/protein/components/ProteinScreen";
import { resultMessages } from "@/i18n/client-messages";

// The protein guide (Plan 9, decision 6b): today's progress for a member and
// higher-protein swaps. Swaps show the member's status, so the screen gets
// the result catalogue (status labels).
export default async function ProteinPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const messages = resultMessages(await getMessages({ locale }));
  return (
    <main className={pageClass}>
      <NextIntlClientProvider locale={locale} messages={messages}>
        <ProteinScreen />
      </NextIntlClientProvider>
    </main>
  );
}
