import { getTranslations, setRequestLocale } from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { RecipeBuilder } from "@/features/recipes/components/RecipeBuilder";

// Personal data is fetched in the browser (the (app) layout is dynamic).
export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations({ locale });
  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("recipes.title")} />
      <RecipeBuilder />
    </main>
  );
}
