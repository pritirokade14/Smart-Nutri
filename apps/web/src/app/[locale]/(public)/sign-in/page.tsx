import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { cardClass } from "@/components/ui/Card";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { LeafIcon } from "@/components/ui/icons";
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
    <main className="mx-auto w-full max-w-md px-4 py-10 md:py-16">
      <div className={`${cardClass} space-y-6 p-6 sm:p-8`}>
        <header className="space-y-3 text-center">
          <span className="mx-auto flex size-12 items-center justify-center rounded-lg bg-brand-primary text-brand-on">
            <LeafIcon className="size-6" />
          </span>
          <h1 className="text-xl font-bold text-text-primary">
            {t("auth.title")}
          </h1>
          <p className="text-md text-text-secondary">{t("auth.subtitle")}</p>
        </header>
        <SignInPanel locale={locale} next={next} />
        <DisclaimerFooter />
      </div>
    </main>
  );
}
