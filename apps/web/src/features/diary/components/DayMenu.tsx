"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { DiaryDayOut } from "../api/diary";
import { useSetPartial } from "../hooks/useDiaryDay";

/**
 * The day menu: Copy yesterday, Copy a day, and "Mark as partly logged" (a
 * switch, with its explanation: a partly logged day is left out of the weekly
 * averages). Managing meals is slice 2b.
 */
export function DayMenu({
  day,
  onCopyYesterday,
  onCopyDay,
}: {
  day: DiaryDayOut;
  onCopyYesterday: () => void;
  onCopyDay: () => void;
}) {
  const t = useTranslations();
  const [open, setOpen] = useState(false);
  const partial = useSetPartial();
  return (
    <div className="relative" data-testid="day-menu">
      <Button
        variant="outline"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        {t("nav.more")}
      </Button>
      {open ? (
        <div
          role="menu"
          className="absolute right-0 z-20 mt-2 w-72 space-y-1 rounded-lg border border-border-default bg-surface-default p-2 shadow-md"
        >
          <button
            type="button"
            role="menuitem"
            className="flex min-h-11 w-full cursor-pointer items-center rounded-md px-3 text-left text-md hover:bg-surface-muted"
            onClick={() => {
              setOpen(false);
              onCopyYesterday();
            }}
          >
            {t("diary.copy_yesterday")}
          </button>
          <button
            type="button"
            role="menuitem"
            className="flex min-h-11 w-full cursor-pointer items-center rounded-md px-3 text-left text-md hover:bg-surface-muted"
            onClick={() => {
              setOpen(false);
              onCopyDay();
            }}
          >
            {t("diary.copy_day")}
          </button>
          <div className="space-y-1 px-3 py-2">
            <label className="flex min-h-11 cursor-pointer items-center gap-3 text-md">
              <input
                type="checkbox"
                checked={day.partial_logged}
                disabled={partial.isPending}
                onChange={(e) =>
                  partial.mutate({ date: day.date, partial: e.target.checked })
                }
              />
              {t("diary.mark_partial")}
            </label>
            <p className="text-sm text-text-secondary">
              {t("diary.partial_note")}
            </p>
            {partial.error ? (
              <p role="alert" className="text-sm text-text-primary">
                {partial.error.code === "network"
                  ? t("meals.online_only")
                  : t(errorKey(t, partial.error))}
              </p>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
