"use client";

import { useLocale, useTranslations } from "next-intl";
import { todayIst } from "@/features/meals/api/meals";
import { useWeekCounts } from "@/features/meals/hooks/useMeals";
import { ShareButton } from "./ShareButton";
import { shareUrl, shareWeeklyText } from "./shareText";

/** "Share our week": the family's counts only (GET /v1/meals/week_counts). */
export function WeeklyShare({ today = todayIst() }: { today?: string }) {
  const t = useTranslations();
  const locale = useLocale();
  const counts = useWeekCounts(today);
  if (!counts.data) return null; // nothing to share until the counts load
  const url = shareUrl(locale, null);
  return (
    <ShareButton
      label={t("share.weekly_button")}
      text={shareWeeklyText(t, counts.data.scans, counts.data.logged, url)}
      url={url}
      event="share_weekly"
    />
  );
}
