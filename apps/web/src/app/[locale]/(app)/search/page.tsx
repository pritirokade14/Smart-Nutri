import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { SearchBox } from "@/features/product/components/SearchBox";

// Product search (ours, then Open Food Facts). The query stays in the page
// state, never in the URL (paths and queries are sent to analytics).
export default function SearchPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations("search");
  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("title")} description={t("hint")} />
      <SearchBox label={t("placeholder")} />
    </main>
  );
}
