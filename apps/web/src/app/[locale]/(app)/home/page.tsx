import { NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { HomeView } from "@/features/home/components/HomeView";
import { membersMessages } from "@/i18n/client-messages";

// Home in the account's focused mode. The allergy card names each member's
// allergies, so the view gets the members catalogue (allergen labels).
export default async function HomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const messages = membersMessages(await getMessages({ locale }));
  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <HomeView />
    </NextIntlClientProvider>
  );
}
