import { getTranslations, setRequestLocale } from "next-intl/server";

// Placeholder: Plan 3 Task 8 replaces this with the verdict page.
export default async function ResultPage({
  params,
}: {
  params: Promise<{ locale: string; barcode: string }>;
}) {
  const { locale, barcode } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  return (
    <main className="mx-auto max-w-xl p-(--spacing-4)">
      <h1 className="text-(length:--text-xl)">{barcode}</h1>
      <p className="text-(length:--text-sm)">{t("common.disclaimer")}</p>
    </main>
  );
}
