"use client";

import { useLocale, useTranslations } from "next-intl";
import { useId } from "react";
import { Button } from "@/components/ui/Button";
import { inputClass } from "@/components/ui/field";
import { ArrowRightIcon } from "@/components/ui/icons";
import { longDateLabel } from "@/features/history/lib/summary";
import { addDays } from "@/features/meals/api/meals";

/**
 * The date switcher: previous and next are the shown date plus or minus one
 * calendar day; next is disabled on the API's `today` (never the browser's
 * clock). A future date cannot be picked.
 */
export function DayHeader({
  date,
  today,
  onDate,
  trailing,
}: {
  date: string;
  today: string;
  onDate: (date: string) => void;
  /** The eye toggle, when the member has a guide. */
  trailing?: React.ReactNode;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const pick = useId();
  const isToday = date === today;
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          aria-label={t("diary.prev_day")}
          onClick={() => onDate(addDays(date, -1))}
        >
          <ArrowRightIcon className="size-4 rotate-180" />
        </Button>
        <h2
          data-testid="day-title"
          data-allow-digits
          className="min-w-32 text-center text-lg font-semibold text-text-primary"
        >
          {isToday ? t("diary.today") : longDateLabel(date, locale)}
        </h2>
        <Button
          variant="outline"
          size="sm"
          aria-label={t("diary.next_day")}
          disabled={isToday}
          onClick={() => onDate(addDays(date, 1))}
        >
          <ArrowRightIcon className="size-4" />
        </Button>
      </div>
      <div className="flex items-center gap-2">
        <label htmlFor={pick} className="sr-only">
          {t("diary.pick_date")}
        </label>
        <input
          id={pick}
          type="date"
          value={date}
          max={today}
          onChange={(e) => {
            const v = e.target.value;
            if (v && v <= today) onDate(v);
          }}
          className={`${inputClass} w-auto`}
        />
        {trailing}
      </div>
    </div>
  );
}
