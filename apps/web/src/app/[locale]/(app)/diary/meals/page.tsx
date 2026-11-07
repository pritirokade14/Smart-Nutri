import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { MealsScreen } from "@/features/diary/components/MealsScreen";

// Manage meals (spec 7.11): reached from the Diary menu and from Profile,
// Diary and daily guide. Personal data is fetched in the browser.
export default function MealsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  return (
    <main className={pageClass}>
      <MealsScreen />
    </main>
  );
}
