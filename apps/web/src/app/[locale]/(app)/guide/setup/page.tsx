import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { GuideSetup } from "@/features/targets/components/GuideSetup";

// Daily guide setup (Plan 10). Reached from the welcome flow
// (?from=welcome), the Today card and Profile. Nothing personal is in the URL.
export default function GuideSetupPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  return (
    <main className={pageClass}>
      <GuideSetup />
    </main>
  );
}
