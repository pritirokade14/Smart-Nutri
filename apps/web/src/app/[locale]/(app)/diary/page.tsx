import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { DiaryView } from "@/features/diary/components/DiaryView";

// The Diary tab (replaces History): one local day of food by meal slot, with
// the daily guide beside it. The date is a query param (`?date=YYYY-MM-DD`):
// route segments carry no values. Personal data is fetched in the browser
// (the (app) layout is dynamic).
export default function DiaryPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ date?: string | string[] }>;
}) {
  const { locale } = use(params);
  const { date } = use(searchParams);
  setRequestLocale(locale);
  return <DiaryView date={typeof date === "string" ? date : undefined} />;
}
