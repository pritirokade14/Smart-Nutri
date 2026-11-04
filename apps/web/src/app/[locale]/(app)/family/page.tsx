import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { MembersList } from "@/features/members/components/MembersList";

// The Family tab: the account's members (the account holder first).
export default function FamilyPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations();
  return (
    <main className={pageClass}>
      <SectionHeader
        as="h1"
        title={t("members.title")}
        description={t("family.body")}
      />
      <MembersList />
    </main>
  );
}
