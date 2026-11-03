import { setRequestLocale } from "next-intl/server";
import { LabelUpload } from "@/features/scan/components/LabelUpload";
import { normalizeBarcode } from "@/features/scan/lib/barcode";

// Label photo capture. `?barcode=` comes from an unknown-barcode result (F15)
// and travels through to the scan and the saved product.
export default async function LabelPage({
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
  return <LabelUpload barcode={code} />;
}
