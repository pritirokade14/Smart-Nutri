import { NextIntlClientProvider } from "next-intl";
import {
  getMessages,
  getTranslations,
  setRequestLocale,
} from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { MemberForm } from "@/features/members/components/MemberForm";
import { membersMessages } from "@/i18n/client-messages";

// Add a family member. The form needs the allergen, diet, condition and alert
// labels, which the root client catalogue leaves out.
export default async function NewMemberPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations({ locale });
  const messages = membersMessages(await getMessages({ locale }));
  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("members.add")} />
      <NextIntlClientProvider locale={locale} messages={messages}>
        <MemberForm />
      </NextIntlClientProvider>
    </main>
  );
}
