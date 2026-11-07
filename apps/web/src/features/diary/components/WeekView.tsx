"use client";

import { useLocale, useTranslations } from "next-intl";
import { chipClass } from "@/components/ui/Chip";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import { formatAmount, shownTotal } from "@/features/history/lib/summary";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { WeeklyShare } from "@/features/share/WeeklyShare";
import type { DayTile, DiaryWeekOut } from "../api/diary";
import { useDiaryWeek } from "../hooks/useDiaryDay";

const AVG = [
  ["energy_kcal", "targets.energy", "targets.kcal_value"],
  ["protein_g", "targets.protein", "targets.g_value"],
  ["carbs_g", "targets.carbs", "targets.g_value"],
  ["fat_g", "targets.fat", "targets.g_value"],
] as const;

// Drawing scale only: a bar fills `progress / CEILING` of its box, and the
// target line sits where progress is 1. The progress itself is the API's.
const CEILING = 1.25;

function dayLabel(date: string, locale: string): string {
  return new Intl.DateTimeFormat(`${locale}-u-nu-latn`, {
    weekday: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${date}T00:00:00Z`));
}

function Tile({
  tile,
  hidden,
  onPick,
}: {
  tile: DayTile;
  hidden: boolean;
  onPick: (date: string) => void;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const progress = tile.progress?.energy_kcal;
  const kcal = shownTotal(
    tile.totals.energy_kcal,
    tile.incomplete.energy_kcal === true,
  );
  const showTarget = tile.targets?.energy_kcal != null && !hidden;
  return (
    <li data-testid="week-tile" data-date={tile.date} className="min-w-0">
      <button
        type="button"
        onClick={() => onPick(tile.date)}
        className="flex w-full cursor-pointer flex-col items-center gap-1 rounded-md p-1 hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-brand-primary"
      >
        <span
          data-allow-digits
          className="text-xs font-semibold text-text-secondary"
        >
          {dayLabel(tile.date, locale)}
        </span>
        <span
          aria-hidden="true"
          className="relative flex h-24 w-6 items-end overflow-hidden rounded-md bg-surface-muted"
        >
          {typeof progress === "number" ? (
            <span
              data-testid="week-bar"
              style={{
                height: `${Math.round((Math.min(progress, CEILING) / CEILING) * 100)}%`,
              }}
              className="w-full bg-brand-primary"
            />
          ) : null}
          {showTarget ? (
            <span
              data-testid="week-target-line"
              style={{ bottom: `${Math.round((1 / CEILING) * 100)}%` }}
              className="absolute inset-x-0 h-0.5 bg-text-primary"
            />
          ) : null}
        </span>
        {kcal !== null ? (
          <span data-testid="week-kcal" className="text-xs text-text-primary">
            {formatAmount(kcal)}
          </span>
        ) : null}
        {tile.incomplete.energy_kcal && tile.items > 0 ? (
          <span
            className={`${chipClass} px-1.5 py-0 text-xs`}
            data-testid="week-incomplete"
            title={t("diary.incomplete")}
          >
            <span className="sr-only">{t("diary.incomplete")}</span>
            <span aria-hidden="true">+</span>
          </span>
        ) : null}
        {tile.partial_logged ? (
          <span
            className={`${chipClass} px-1.5 py-0 text-xs`}
            data-testid="week-partial"
          >
            {t("diary.partial_badge")}
          </span>
        ) : null}
      </button>
    </li>
  );
}

/**
 * Seven tiles (oldest first) from GET /v1/diary/week: energy bars against each
 * day's own frozen target line, partial and incomplete markers, the averages
 * over the logged days, and how many of them reached the protein guide. No
 * rating text and no streak. With hidden numbers there are bar shapes only:
 * no averages and no protein count.
 */
export function WeekView({
  onPickDay,
  today,
}: {
  onPickDay: (date: string) => void;
  today?: string;
}) {
  const t = useTranslations();
  const week = useDiaryWeek();
  if (week.isPending) return <LoadingState label={t("common.loading")} />;
  if (week.isError)
    return (
      <ErrorState
        message={t(errorKey(t, week.error))}
        onRetry={() => void week.refetch()}
        retrying={week.isFetching}
      />
    );
  const w: DiaryWeekOut = week.data;
  const hidden = w.numbers_hidden.energy || w.numbers_hidden.macros;
  const anyAverage = AVG.some(([k]) => w.averages[k] !== null);
  return (
    <section
      className="space-y-4"
      data-testid="week-view"
      aria-label={t("diary.week.title")}
    >
      <h2 className="text-lg font-semibold text-text-primary">
        {t("diary.week.title")}
      </h2>
      <ul className="grid grid-cols-7 gap-1">
        {w.days.map((d) => (
          <Tile key={d.date} tile={d} hidden={hidden} onPick={onPickDay} />
        ))}
      </ul>
      {w.averaged_days > 0 && anyAverage ? (
        <div className="space-y-2" data-testid="week-averages">
          <p className="text-md font-semibold text-text-primary">
            <span data-allow-digits>
              {t("diary.week.average", { days: w.averaged_days })}
            </span>
          </p>
          <ul className="space-y-1">
            {AVG.map(([k, label, unit]) => {
              const v = w.averages[k];
              if (v === null) return null;
              return (
                <li
                  key={k}
                  data-testid={`week-average-${k}`}
                  className="flex flex-wrap items-center justify-between gap-2 text-md"
                >
                  <span className="text-text-secondary">{t(label)}</span>
                  <span className="flex items-center gap-2 text-text-primary">
                    {w.averages_incomplete[k] ? (
                      <span
                        data-testid={`week-at-least-${k}`}
                        className="text-text-secondary"
                      >
                        {t("diary.week.at_least", {
                          value: t(unit, { value: formatAmount(v) }),
                        })}
                      </span>
                    ) : (
                      t(unit, { value: formatAmount(v) })
                    )}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
      {w.averaged_days > 0 && !w.numbers_hidden.macros ? (
        <p
          data-testid="week-protein-days"
          data-allow-digits
          className="text-md text-text-primary"
        >
          {t("diary.week.protein_days", {
            met: w.protein_met_days,
            days: w.averaged_days,
          })}
        </p>
      ) : null}
      <WeeklyShare today={today} label={t("diary.share_week")} />
      <div className="space-y-1">
        {!hidden && w.days.some((d) => d.targets !== null) ? (
          <p className="text-sm text-text-secondary">
            {t("targets.pending_review")}
          </p>
        ) : null}
      </div>
    </section>
  );
}
