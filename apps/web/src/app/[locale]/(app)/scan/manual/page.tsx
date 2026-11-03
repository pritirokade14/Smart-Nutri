import { setRequestLocale } from "next-intl/server";
import { ConfirmScreen } from "@/features/scan/components/ConfirmScreen";
import { normalizeBarcode } from "@/features/scan/lib/barcode";

// "Enter manually": an EMPTY form with no scan id; every value is typed.
export default async function ManualEntryPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ barcode?: string | string[] }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const { barcode } = await searchParams;
  const code = typeof barcode === "string" ? normalizeBarcode(barcode) : null;
  return <ConfirmScreen scanId={null} barcode={code} />;
}
