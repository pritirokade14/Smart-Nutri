import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { SignInPanel } from "@/features/auth/components/SignInPanel";

export default function SignInPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ next?: string }>;
}) {
  const { locale } = use(params);
  const { next } = use(searchParams);
  setRequestLocale(locale);
  const t = useTranslations();
  return (
    <main className="mx-auto flex max-w-sm flex-col gap-(--spacing-4) p-(--spacing-4)">
      <h1 className="text-(length:--text-xl)">{t("auth.title")}</h1>
      <SignInPanel locale={locale} next={next} />
      <p className="text-(length:--text-sm)">{t("common.disclaimer")}</p>
    </main>
  );
}
