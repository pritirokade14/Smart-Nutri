"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useLocale, useTranslations } from "next-intl";
import { ApiError, fetchMe } from "@/features/me/api/me";

export default function HomePage() {
  const t = useTranslations();
  const locale = useLocale();
  const { data, error, isPending } = useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
  });

  if (isPending) return <p>{t("common.loading")}</p>;
  if (error) {
    const code = error instanceof ApiError ? error.code : "internal_error";
    return (
      <p role="alert">
        {t.has(`error.${code}`)
          ? t(`error.${code}`)
          : t("error.internal_error")}
      </p>
    );
  }
  return (
    <main className="mx-auto max-w-xl p-(--spacing-4)">
      <h1 className="text-(length:--text-xl)">
        {t("home.welcome", { name: data.display_name ?? data.email ?? "" })}
      </h1>
      <Link
        href={`/${locale}/scan`}
        className="text-(length:--text-md) underline"
      >
        {t("home.scan_cta")}
      </Link>
      <p className="text-(length:--text-sm)">{t("common.disclaimer")}</p>
    </main>
  );
}
