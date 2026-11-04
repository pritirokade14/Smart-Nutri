import type { Metadata } from "next";
import { useTranslations } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { use } from "react";
import { buttonClass } from "@/components/ui/Button";
import { cardClass } from "@/components/ui/Card";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import {
  ArrowRightIcon,
  CameraIcon,
  FamilyIcon,
  LeafIcon,
  PencilIcon,
  ScanIcon,
} from "@/components/ui/icons";
import { localeAlternates, metadataBase } from "@/lib/seo";

type Params = Promise<{ locale: string }>;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale });
  return {
    metadataBase: metadataBase(),
    title: t("landing.meta_title"),
    description: t("landing.meta_description"),
    alternates: localeAlternates(locale, (l) => `/${l}`),
  };
}

const STEPS = [
  { n: 1, Icon: ScanIcon, title: "step1_title", body: "step1_body" },
  { n: 2, Icon: PencilIcon, title: "step2_title", body: "step2_body" },
  { n: 3, Icon: FamilyIcon, title: "step3_title", body: "step3_body" },
] as const;

// Generic product information only: no session, no member data, no results.
export default function LandingPage({ params }: { params: Params }) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations("landing");
  return (
    <main>
      <section className="border-b border-border-default bg-surface-default">
        <div className="mx-auto grid w-full max-w-6xl items-center gap-10 px-4 py-12 md:grid-cols-[1.2fr_1fr] md:px-6 md:py-20">
          <div className="space-y-5">
            <p className="inline-flex items-center gap-2 rounded-full bg-brand-soft px-3 py-1 text-sm font-semibold text-brand-primary">
              <LeafIcon className="size-4" />
              {t("eyebrow")}
            </p>
            <h1 className="text-2xl leading-tight font-bold text-balance text-text-primary sm:text-3xl">
              {t("hero_title")}
            </h1>
            <p className="max-w-xl text-lg text-text-secondary">
              {t("hero_body")}
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <a
                href={`/${locale}/sign-in`}
                className={buttonClass({ size: "lg" })}
              >
                {t("cta_start")}
                <ArrowRightIcon />
              </a>
              <a
                href="#how"
                className={buttonClass({ variant: "outline", size: "lg" })}
              >
                {t("how_title")}
              </a>
            </div>
          </div>
          {/* Decorative: the three ways in, as icons. */}
          <div aria-hidden="true" className="relative mx-auto w-full max-w-sm">
            <div className="aspect-square rounded-xl bg-brand-soft p-8">
              <div className="grid h-full grid-cols-2 grid-rows-2 gap-4">
                <div className="col-span-2 flex items-center justify-center rounded-lg bg-surface-default text-brand-primary shadow-sm">
                  <ScanIcon className="size-16" />
                </div>
                <div className="flex items-center justify-center rounded-lg bg-surface-default text-brand-primary shadow-sm">
                  <CameraIcon className="size-10" />
                </div>
                <div className="flex items-center justify-center rounded-lg bg-brand-primary text-brand-on shadow-sm">
                  <FamilyIcon className="size-10" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        id="how"
        aria-labelledby="how-title"
        className="mx-auto w-full max-w-6xl scroll-mt-20 space-y-6 px-4 py-12 md:px-6 md:py-16"
      >
        <h2 id="how-title" className="text-xl font-bold text-text-primary">
          {t("how_title")}
        </h2>
        <ol className="grid gap-4 md:grid-cols-3">
          {STEPS.map(({ n, Icon, title, body }) => (
            <li key={n} className={`${cardClass} space-y-3 p-5`}>
              <div className="flex items-center gap-3">
                <span className="flex size-10 items-center justify-center rounded-full bg-brand-primary text-md font-bold text-brand-on">
                  {n}
                </span>
                <Icon className="size-5 text-brand-primary" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary">
                {t(title)}
              </h3>
              <p className="text-md text-text-secondary">{t(body)}</p>
            </li>
          ))}
        </ol>
        <DisclaimerFooter />
      </section>
    </main>
  );
}
