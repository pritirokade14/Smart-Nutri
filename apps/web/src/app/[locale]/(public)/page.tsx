import Link from "next/link";
import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";

export default function LandingPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations();
  return (
    <main className="mx-auto max-w-xl p-(--spacing-4)">
      <h1 className="text-(length:--text-xl)">{t("app.name")}</h1>
      <p className="text-(length:--text-sm)">{t("common.disclaimer")}</p>
      <Link
        href={`/${locale}/sign-in`}
        className="text-(length:--text-md) underline"
      >
        {t("auth.title")}
      </Link>
    </main>
  );
}
