"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/Dialog";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { WeightOut } from "../api/weights";
import { useDeleteWeight, useWeightList } from "../hooks/useWeights";
import { formatDate, formatWeight } from "../lib/format";
import { WeighInDialog } from "./WeighInDialog";

/**
 * The recent weigh-ins, newest first, each with edit and delete. Under hidden
 * numbers a row shows its date only. Without health_data the list is gated
 * (the Progress view shows the consent card instead); erasing everything from
 * that card is `useDeleteAllWeights`.
 */
export function WeightList({ today }: { today: string }) {
  const t = useTranslations();
  const locale = useLocale();
  const list = useWeightList();
  const remove = useDeleteWeight();
  const [editing, setEditing] = useState<WeightOut | null>(null);
  const [deleting, setDeleting] = useState<WeightOut | null>(null);

  if (list.isPending) return <LoadingState label={t("common.loading")} />;
  if (list.isError)
    return (
      <ErrorState
        message={t(errorKey(t, list.error))}
        onRetry={() => void list.refetch()}
        retrying={list.isFetching}
      />
    );
  const items = [...list.data.items].reverse();
  return (
    <div className="space-y-3" data-testid="weight-list">
      {items.length === 0 ? (
        <p data-testid="weight-empty" className="text-md text-text-secondary">
          {t("weight.empty")}
        </p>
      ) : (
        <ul className="divide-y divide-border-default">
          {items.map((w) => (
            <li
              key={w.date}
              data-testid="weight-row"
              data-date={w.date}
              className="flex flex-wrap items-center justify-between gap-2 py-2"
            >
              <span className="text-md text-text-primary">
                <span data-allow-digits>{formatDate(w.date, locale)}</span>
                {w.weight_kg != null && !w.numbers_hidden ? (
                  <span
                    data-testid="weight-row-kg"
                    className="ms-3 font-semibold"
                  >
                    {t("weight.kg_value", { value: formatWeight(w.weight_kg) })}
                  </span>
                ) : null}
              </span>
              <span className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  data-testid="weight-edit"
                  onClick={() => setEditing(w)}
                >
                  {t("weight.edit")}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  data-testid="weight-delete"
                  onClick={() => setDeleting(w)}
                >
                  {t("weight.delete")}
                </Button>
              </span>
            </li>
          ))}
        </ul>
      )}
      {remove.error ? (
        <p role="alert" className="text-md text-text-primary">
          {remove.error.code === "network"
            ? t("meals.online_only")
            : t(errorKey(t, remove.error))}
        </p>
      ) : null}
      {editing ? (
        <WeighInDialog
          key={editing.date}
          today={today}
          existing={{ date: editing.date, weight_kg: editing.weight_kg }}
          onClose={() => setEditing(null)}
        />
      ) : null}
      {deleting ? (
        <ConfirmDialog
          message={t("weight.delete_confirm")}
          confirmLabel={t("weight.delete")}
          cancelLabel={t("common.cancel")}
          busy={remove.isPending}
          onCancel={() => setDeleting(null)}
          onConfirm={() =>
            remove.mutate(deleting.date, {
              onSettled: () => setDeleting(null),
            })
          }
        />
      ) : null}
    </div>
  );
}
