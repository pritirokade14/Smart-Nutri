import { setRequestLocale } from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { ProteinView } from "@/features/protein/components/ProteinView";

// The protein guide (Plan 9, decision 6b): today's progress for a member.
export default async function ProteinPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  return (
    <main className={pageClass}>
      <ProteinView />
    </main>
  );
}
