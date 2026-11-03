import { NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { WelcomeFlow } from "@/features/user-types/components/WelcomeFlow";
import { membersMessages } from "@/i18n/client-messages";

// "What brings you to SmartNutri?" (Plan 9). Right after the terms step on
// first sign-in, and from Profile with ?edit=1. The follow-ups and the
// pre-fill review need the condition, allergen, diet and alert labels, which
// the root client catalogue leaves out.
export default async function WelcomePage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const edit = (await searchParams).edit === "1";
  const messages = membersMessages(await getMessages({ locale }));
  return (
    <main className={pageClass}>
      <NextIntlClientProvider locale={locale} messages={messages}>
        <WelcomeFlow edit={edit} />
      </NextIntlClientProvider>
    </main>
  );
}
