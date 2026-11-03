import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { HistoryView } from "@/features/history/components/HistoryView";

// The History tab (same tab on Android): a member's logged food, the day's
// totals against the daily limits and the last 7 days. Personal data is
// fetched per request in the browser (the (app) layout is dynamic).
export default function HistoryPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  return <HistoryView />;
}
