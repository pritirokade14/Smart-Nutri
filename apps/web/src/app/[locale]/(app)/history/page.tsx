import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { buttonClass } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { HistoryIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";

// Placeholder until the history feature ships (same tab on Android).
export default function HistoryPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations();
  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("history.title")} />
      <EmptyState
        icon={<HistoryIcon />}
        title={t("common.coming_soon")}
        description={t("history.body")}
        action={
          <a href={`/${locale}/scan`} className={buttonClass()}>
            {t("home.scan_cta")}
          </a>
        }
      />
    </main>
  );
}
