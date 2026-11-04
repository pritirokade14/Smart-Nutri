"use client";

import { useLocale, useTranslations } from "next-intl";
import { type ReactNode, useId, useState } from "react";
import { pageClass } from "@/components/shell/page";
import { Button } from "@/components/ui/Button";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { ErrorState } from "@/components/ui/ErrorState";
import { inputClass, labelClass } from "@/components/ui/field";
import { ArrowRightIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState } from "@/components/ui/Skeleton";
import { addDays, todayIst } from "@/features/meals/api/meals";
import { useSummary } from "@/features/meals/hooks/useMeals";
import { useMembers } from "@/features/members/hooks/useMembers";
import type { ApiError } from "@/lib/api/errors";
import { longDateLabel } from "../lib/summary";
import { DayList } from "./DayList";
import { DayTotals } from "./DayTotals";
import { WeeklyDashboard } from "./WeeklyDashboard";

/**
 * The History tab: for one family member, a day's totals against the daily
 * limits and what was eaten (today first, then earlier days), and the last
 * 7 days. Everything is rendered as the API returned it.
 */
export function HistoryView({
  today = todayIst(),
  weekAction,
}: {
  /** Today's IST date; injectable for tests. */
  today?: string;
  /** Extra content under the weekly dashboard (the weekly share). */
  weekAction?: ReactNode;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const memberSelect = useId();
  const members = useMembers();
  const [picked, setPicked] = useState<string | undefined>(undefined);
  const [date, setDate] = useState(today);
  const memberId = picked ?? members.data?.[0]?.id;
  const day = useSummary(memberId, "day", date);
  const week = useSummary(memberId, "week", today);

  const errorText = (e: ApiError) =>
    t.has(`error.${e.code}`) ? t(`error.${e.code}`) : t("error.internal_error");

  let body: ReactNode;
  if (members.isPending) {
    body = <LoadingState label={t("common.loading")} />;
  } else if (members.isError) {
    body = (
      <ErrorState
        message={errorText(members.error)}
        onRetry={() => members.refetch()}
        retrying={members.isFetching}
      />
    );
  } else if (memberId) {
    const isToday = date >= today;
    body = (
      <>
        {members.data.length > 1 ? (
          <div className="space-y-1">
            <label htmlFor={memberSelect} className={labelClass}>
              {t("history.member")}
            </label>
            <select
              id={memberSelect}
              value={memberId}
              onChange={(e) => setPicked(e.target.value)}
              className={inputClass}
            >
              {members.data.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name.trim() !== ""
                    ? m.name
                    : m.is_primary
                      ? t("result.you")
                      : t(`share.relation.${m.relation}`)}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        <section aria-labelledby="day-title" className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <Button
              variant="outline"
              size="sm"
              aria-label={t("history.previous_day")}
              onClick={() => setDate((d) => addDays(d, -1))}
            >
              <ArrowRightIcon className="size-4 rotate-180" />
            </Button>
            <h2
              id="day-title"
              data-testid="day-title"
              className="text-lg font-semibold text-text-primary"
            >
              {isToday ? t("history.today") : longDateLabel(date, locale)}
            </h2>
            <Button
              variant="outline"
              size="sm"
              aria-label={t("history.next_day")}
              disabled={isToday}
              onClick={() => setDate((d) => addDays(d, 1))}
            >
              <ArrowRightIcon className="size-4" />
            </Button>
          </div>
          {day.isPending ? (
            <LoadingState label={t("common.loading")} lines={1} />
          ) : day.isError ? (
            <ErrorState
              message={errorText(day.error)}
              onRetry={() => day.refetch()}
              retrying={day.isFetching}
            />
          ) : (
            <DayTotals summary={day.data} />
          )}
          <h3 className="text-md font-semibold text-text-secondary">
            {t("history.logged_title")}
          </h3>
          <DayList memberId={memberId} date={date} />
        </section>

        {week.isPending ? (
          <LoadingState label={t("common.loading")} lines={2} />
        ) : week.isError ? (
          <ErrorState
            message={errorText(week.error)}
            onRetry={() => week.refetch()}
            retrying={week.isFetching}
          />
        ) : (
          <WeeklyDashboard summary={week.data} />
        )}
        {weekAction}
      </>
    );
  }

  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("history.title")} />
      {body}
      <DisclaimerFooter />
    </main>
  );
}
