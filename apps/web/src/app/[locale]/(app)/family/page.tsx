import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { EmptyState } from "@/components/ui/EmptyState";
import { FamilyIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";

// Placeholder until the family members feature ships (same tab on Android).
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
      <SectionHeader as="h1" title={t("family.title")} />
      <EmptyState
        icon={<FamilyIcon />}
        title={t("common.coming_soon")}
        description={t("family.body")}
      />
    </main>
  );
}
