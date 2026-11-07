import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { GuideSettings } from "@/features/targets/components/GuideSettings";

// "Diary and daily guide" settings (Plan 10), under Profile.
export default function GuideSettingsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  return (
    <main className={pageClass}>
      <GuideSettings />
    </main>
  );
}
