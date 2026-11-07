import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { CustomFoodForm } from "@/features/foods/components/CustomFoodForm";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// The URL carries only the id. Personal data is fetched in the browser.
export default async function Page({
  params,
}: {
  params: Promise<{ locale: string; id: string }>;
}) {
  const { locale, id } = await params;
  setRequestLocale(locale);
  if (!UUID.test(id)) notFound();
  const t = await getTranslations({ locale });
  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("custom_food.title")} />
      <CustomFoodForm id={id.toLowerCase()} />
    </main>
  );
}
