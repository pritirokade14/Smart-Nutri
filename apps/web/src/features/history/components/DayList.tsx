"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { cardClass } from "@/components/ui/Card";
import { chipClass } from "@/components/ui/Chip";
import { ConfirmDialog } from "@/components/ui/Dialog";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import { OffAttribution } from "@/features/analysis/components/OffAttribution";
import type { MealOut } from "@/features/meals/api/meals";
import { useDeleteMeal, useMealsForDay } from "@/features/meals/hooks/useMeals";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/cn";
import { formatAmount } from "../lib/summary";

function timeLabel(iso: string, locale: string): string {
  return new Intl.DateTimeFormat(`${locale}-u-nu-latn`, {
    hour: "numeric",
    minute: "2-digit",
    timeZone: "Asia/Kolkata",
  }).format(new Date(iso));
}

/** One member's logged items for one IST day, newest first, with remove. */
export function DayList({
  memberId,
  date,
}: {
  memberId: string;
  date: string;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const meals = useMealsForDay(memberId, date);
  const remove = useDeleteMeal();
  const [confirm, setConfirm] = useState<MealOut | null>(null);

  const errorText = (e: ApiError) =>
    t.has(`error.${e.code}`) ? t(`error.${e.code}`) : t("error.internal_error");

  if (meals.isPending)
    return <LoadingState label={t("common.loading")} lines={1} />;
  if (meals.isError) {
    return (
      <ErrorState
        message={errorText(meals.error)}
        onRetry={() => meals.refetch()}
        retrying={meals.isFetching}
      />
    );
  }
  if (meals.data.length === 0) {
    return (
      <p data-testid="day-list-empty" className="text-md text-text-secondary">
        {t("history.empty")}
      </p>
    );
  }
  const anyGrade = meals.data.some((m) => m.grade);
  const fromOff = meals.data.some((m) => m.attribution != null);
  return (
    <div className="space-y-2">
      <ul
        data-testid="day-list"
        className={cn(cardClass, "divide-y divide-border-default")}
      >
        {meals.data.map((m) => (
          <li
            key={m.id}
            data-testid="meal-row"
            className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 sm:px-5"
          >
            <div className="min-w-0 space-y-0.5">
              <p className="text-md font-semibold break-words text-text-primary">
                {m.product_name}
              </p>
              <p className="flex flex-wrap gap-x-3 text-sm text-text-secondary">
                <span>{timeLabel(m.eaten_at, locale)}</span>
                <span>
                  {t("history.item_amount", { grams: formatAmount(m.grams) })}
                </span>
              </p>
            </div>
            <div className="flex items-center gap-2">
              {m.grade ? (
                <span className={chipClass}>
                  {t("result.grade", { grade: m.grade })}
                </span>
              ) : null}
              <Button variant="ghost" size="sm" onClick={() => setConfirm(m)}>
                {t("history.remove")}
              </Button>
            </div>
          </li>
        ))}
      </ul>
      {remove.isError ? (
        <p role="alert" className="text-md text-text-primary">
          {errorText(remove.error)}
        </p>
      ) : null}
      {anyGrade ? (
        <p className="text-sm text-text-secondary">
          {t("nutriscore.calculated_by")}
        </p>
      ) : null}
      {fromOff ? <OffAttribution barcode={null} /> : null}
      {confirm ? (
        <ConfirmDialog
          message={t("history.remove_confirm")}
          confirmLabel={t("history.remove")}
          cancelLabel={t("common.cancel")}
          busy={remove.isPending}
          onCancel={() => setConfirm(null)}
          onConfirm={() =>
            remove.mutate(confirm.id, {
              onSuccess: () => track("meal_removed"),
              onSettled: () => setConfirm(null),
            })
          }
        />
      ) : null}
    </div>
  );
}
