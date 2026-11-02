import { useTranslations } from "next-intl";

export default function NotFound() {
  const t = useTranslations();
  return (
    <main className="mx-auto max-w-xl p-(--spacing-4)">
      <h1 className="text-(length:--text-xl)">{t("error.not_found")}</h1>
    </main>
  );
}
