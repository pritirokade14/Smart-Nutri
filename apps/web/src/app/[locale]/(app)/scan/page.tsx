"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { pageClass } from "@/components/shell/page";
import { Card, cardClass } from "@/components/ui/Card";
import { ArrowRightIcon, CameraIcon, SearchIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { BarcodeScanner } from "@/features/scan/components/BarcodeScanner";
import { ManualBarcodeForm } from "@/features/scan/components/ManualBarcodeForm";
import { cn } from "@/lib/cn";

export default function ScanPage() {
  const t = useTranslations("scan");
  const tLabel = useTranslations("label");
  const tSearch = useTranslations("search");
  const locale = useLocale();
  const router = useRouter();
  const go = (code: string) => router.push(`/${locale}/result/${code}`);
  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("title")} description={t("subtitle")} />
      <Card padded={false} className="overflow-hidden">
        <BarcodeScanner onCode={go} />
      </Card>
      <Card>
        <ManualBarcodeForm onSubmit={go} />
      </Card>
      <a
        href={`/${locale}/scan/label`}
        className={cn(
          cardClass,
          "group flex items-center gap-4 p-4 transition-colors hover:border-brand-primary sm:p-5",
        )}
      >
        <span className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-brand-primary">
          <CameraIcon />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-md font-semibold text-text-primary">
            {tLabel("title")}
          </span>
          <span className="block text-sm text-text-secondary">
            {t("label_hint")}
          </span>
        </span>
        <ArrowRightIcon className="size-5 shrink-0 text-text-secondary" />
      </a>
      <a
        href={`/${locale}/search`}
        className={cn(
          cardClass,
          "group flex items-center gap-4 p-4 transition-colors hover:border-brand-primary sm:p-5",
        )}
      >
        <span className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-brand-soft text-brand-primary">
          <SearchIcon />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-md font-semibold text-text-primary">
            {tSearch("title")}
          </span>
          <span className="block text-sm text-text-secondary">
            {tSearch("hint")}
          </span>
        </span>
        <ArrowRightIcon className="size-5 shrink-0 text-text-secondary" />
      </a>
    </main>
  );
}
