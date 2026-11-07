import { redirect } from "next/navigation";

// History became the Diary (Plan 11): old links and bookmarks land there.
export default async function HistoryPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  redirect(`/${locale}/diary`);
}
