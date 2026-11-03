import type { Metadata } from "next";
import { useTranslations } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

type Params = Promise<{ locale: string }>;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale });
  return { title: t("goodbye.meta_title"), robots: { index: false } };
}

// After DELETE /v1/me: public (the session is gone), generic text only.
export default function GoodbyePage({ params }: { params: Params }) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations();
  return (
    <main className={`${pageClass} px-4 py-12 md:px-6`}>
      <Card as="section" className="space-y-4" data-testid="goodbye">
        <h1 className="text-xl font-bold text-text-primary sm:text-2xl">
          {t("goodbye.title")}
        </h1>
        <p className="text-md text-text-primary">{t("goodbye.body")}</p>
        <a href={`/${locale}`} className={buttonClass({ variant: "outline" })}>
          {t("common.go_home")}
        </a>
      </Card>
    </main>
  );
}
