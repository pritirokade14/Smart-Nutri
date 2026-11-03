import { notFound } from "next/navigation";
import { NextIntlClientProvider } from "next-intl";
import {
  getMessages,
  getTranslations,
  setRequestLocale,
} from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { MemberEditor } from "@/features/members/components/MemberEditor";
import { membersMessages } from "@/i18n/client-messages";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// Edit one member. The URL carries only the member's id, never a name.
export default async function EditMemberPage({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  if (!UUID.test(id)) notFound();
  const t = await getTranslations({ locale });
  const messages = membersMessages(await getMessages({ locale }));
  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("members.edit")} />
      <NextIntlClientProvider locale={locale} messages={messages}>
        <MemberEditor id={id.toLowerCase()} />
      </NextIntlClientProvider>
    </main>
  );
}
