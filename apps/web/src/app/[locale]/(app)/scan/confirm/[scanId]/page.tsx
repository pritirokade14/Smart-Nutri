import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";
import { ConfirmScreen } from "@/features/scan/components/ConfirmScreen";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// The confirm step for one label scan. The draft itself is held in memory by
// the client (handed over from the upload page); the URL carries only the id.
export default async function ConfirmPage({
  params,
}: {
  params: Promise<{ locale: string; scanId: string }>;
}) {
  const { locale, scanId } = await params;
  setRequestLocale(locale);
  if (!UUID.test(scanId)) notFound();
  return <ConfirmScreen scanId={scanId.toLowerCase()} />;
}
