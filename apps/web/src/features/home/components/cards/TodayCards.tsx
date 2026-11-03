"use client";

import { useLocale, useTranslations } from "next-intl";
import { ArrowRightIcon } from "@/components/ui/icons";
import { BandBadge } from "@/features/history/components/BandBadge";
import {
  formatAmount,
  readBand,
  readFlag,
  readTotal,
  shownBand,
  shownTotal,
} from "@/features/history/lib/summary";
import { todayIst } from "@/features/meals/api/meals";
import {
  useMealsForDay,
  useSummary,
  useWeekCounts,
} from "@/features/meals/hooks/useMeals";
import type { MemberOut } from "@/features/members/api/members";
import { ProteinProgress } from "@/features/protein/components/ProteinProgress";
import { CardShell, QueryBody } from "./CardShell";

/** Today's sugar and salt for the account holder, with the API's bands. */
export function TodaySugarSaltCard({ primary }: { primary?: MemberOut }) {
  const t = useTranslations();
  const summary = useSummary(primary?.id, "day", todayIst());
  const rows = [
    { key: "sugars_g", band: "sugar_g", limit: "sugar_g" },
    { key: "salt_g", band: "salt_g", limit: "salt_g" },
  ] as const;
  return (
    <CardShell
      card="today_sugar_salt"
      title={t("home.cards.today_sugar_salt.title")}
    >
      <QueryBody
        query={summary}
        render={(s) => (
          <ul className="divide-y divide-border-default">
            {rows.map((r) => {
              const total = shownTotal(
                readTotal(s.totals, r.key),
                readFlag(s.incomplete, r.key),
              );
              const limit = s.limits[r.limit];
              return (
                <li
                  key={r.key}
                  className="flex flex-wrap items-center justify-between gap-2 py-2"
                >
                  <div>
                    <p className="text-sm font-semibold text-text-secondary">
                      {t(`summary.nutrient.${r.key}`)}
                    </p>
                    <p className="text-md text-text-primary">
                      {total === null
                        ? t("summary.band.unknown")
                        : limit == null
                          ? t("summary.total_g", { total: formatAmount(total) })
                          : t("summary.total_of_limit", {
                              total: formatAmount(total),
                              limit: formatAmount(limit),
                            })}
                    </p>
                  </div>
                  <BandBadge
                    band={shownBand(readBand(s.bands, r.band), total)}
                  />
                </li>
              );
            })}
          </ul>
        )}
      />
    </CardShell>
  );
}

/** Today's protein for the account holder (the guide, never a verdict). */
export function TodayProteinCard({ primary }: { primary?: MemberOut }) {
  const t = useTranslations();
  const locale = useLocale();
  const summary = useSummary(primary?.id, "day", todayIst());
  return (
    <CardShell card="today_protein" title={t("home.cards.today_protein.title")}>
      <QueryBody
        query={summary}
        render={(s) => (
          <ProteinProgress summary={s} member={primary} locale={locale} />
        )}
      />
    </CardShell>
  );
}

/** The family's logged-item count for the last 7 days (counts only). */
export function WeeklyFamilyCard() {
  const t = useTranslations();
  const counts = useWeekCounts(todayIst());
  return (
    <CardShell card="weekly_family" title={t("home.cards.weekly_family.title")}>
      <QueryBody
        query={counts}
        render={(c) => (
          <p className="text-md text-text-primary">
            {t("home.cards.weekly_family.body", { count: c.logged })}
          </p>
        )}
      />
    </CardShell>
  );
}

/**
 * Recent items. The API has no list of past scans, so this is what the
 * account holder logged today (meals_list), linking to History; always last.
 */
export function RecentScansCard({ primary }: { primary?: MemberOut }) {
  const t = useTranslations();
  const locale = useLocale();
  const meals = useMealsForDay(primary?.id, todayIst());
  return (
    <CardShell card="recent_scans" title={t("home.cards.recent_scans.title")}>
      <QueryBody
        query={meals}
        render={(list) =>
          list.length === 0 ? (
            <div className="space-y-1">
              <p className="text-md font-semibold text-text-primary">
                {t("home.recent_empty_title")}
              </p>
              <p className="text-sm text-text-secondary">
                {t("home.recent_empty_body")}
              </p>
            </div>
          ) : (
            <ul className="divide-y divide-border-default">
              {list.slice(0, 5).map((m) => (
                <li key={m.id} className="py-2">
                  {m.product_id ? (
                    <a
                      href={`/${locale}/product/${m.product_id}`}
                      className="text-md text-text-primary hover:underline"
                    >
                      {m.product_name}
                    </a>
                  ) : (
                    <span className="text-md text-text-primary">
                      {m.product_name}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )
        }
      />
      <a
        href={`/${locale}/history`}
        className="inline-flex min-h-11 items-center gap-2 text-md font-semibold text-brand-primary"
      >
        {t("nav.history")}
        <ArrowRightIcon className="size-4 shrink-0" />
      </a>
    </CardShell>
  );
}
