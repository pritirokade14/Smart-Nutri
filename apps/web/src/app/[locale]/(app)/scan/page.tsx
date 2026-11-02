"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { BarcodeScanner } from "@/features/scan/components/BarcodeScanner";
import { ManualBarcodeForm } from "@/features/scan/components/ManualBarcodeForm";

export default function ScanPage() {
  const t = useTranslations("scan");
  const locale = useLocale();
  const router = useRouter();
  const go = (code: string) => router.push(`/${locale}/result/${code}`);
  return (
    <main className="mx-auto flex max-w-xl flex-col gap-(--spacing-4) p-(--spacing-4)">
      <h1 className="text-(length:--text-xl)">{t("title")}</h1>
      <BarcodeScanner onCode={go} />
      <ManualBarcodeForm onSubmit={go} />
    </main>
  );
}
