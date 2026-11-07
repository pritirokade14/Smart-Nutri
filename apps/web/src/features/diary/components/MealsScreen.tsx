"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button, buttonClass } from "@/components/ui/Button";
import { Card, cardClass } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/Dialog";
import { ErrorState } from "@/components/ui/ErrorState";
import { hintClass, inputClass } from "@/components/ui/field";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState } from "@/components/ui/Skeleton";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/cn";
import {
  useArchiveMealSlot,
  useCreateMealSlot,
  useMealSlots,
  useRenameMealSlot,
  useReorderMealSlots,
} from "../hooks/useMealSlots";
import { clampLabel, MAX_LABEL, MealSlotRow } from "./MealSlotRow";

const MAX_SLOTS = 6;

/**
 * Manage meals (spec 7.11): list, add (at most 6), rename (30 characters),
 * reorder and remove. Online only. Labels are the user's own text: never
 * translated and never sent to analytics (this screen tracks nothing). No
 * numbers appear here.
 */
export function MealsScreen() {
  const t = useTranslations();
  const locale = useLocale();
  const slots = useMealSlots(false);
  const create = useCreateMealSlot();
  const rename = useRenameMealSlot();
  const reorder = useReorderMealSlots();
  const archive = useArchiveMealSlot();
  const [label, setLabel] = useState("");
  const [rowError, setRowError] = useState<{ id: string; text: string } | null>(
    null,
  );
  const [addError, setAddError] = useState<string | null>(null);
  const [removing, setRemoving] = useState<string | null>(null);
  const [dragId, setDragId] = useState<string | null>(null);

  const errorText = (e: ApiError): string => {
    if (e.code === "network") return t("meals.online_only");
    if (e.code === "meal_slot_label_duplicate")
      return t("diary.slots.duplicate");
    if (e.code === "meal_slot_limit_reached")
      return t("diary.slots.limit", { max: MAX_SLOTS });
    if (e.code === "meal_slot_last_active") return t("diary.slots.last_active");
    return t(errorKey(t, e));
  };

  if (slots.isPending) return <LoadingState label={t("common.loading")} />;
  if (slots.isError)
    return (
      <ErrorState
        message={errorText(slots.error)}
        onRetry={() => void slots.refetch()}
      />
    );

  const items = [...slots.data.items]
    .filter((s) => !s.archived)
    .sort((a, b) => a.position - b.position);
  const full = items.length >= MAX_SLOTS;
  const busy =
    create.isPending ||
    rename.isPending ||
    reorder.isPending ||
    archive.isPending;

  const move = (from: number, to: number) => {
    if (to < 0 || to >= items.length || from === to) return;
    const ids = items.map((s) => s.id);
    const [id] = ids.splice(from, 1);
    ids.splice(to, 0, id as string);
    setRowError(null);
    reorder.mutate(ids, {
      onError: (e) =>
        setRowError({ id: items[from]?.id ?? "", text: errorText(e) }),
    });
  };

  const patch = (
    id: string,
    body: Parameters<typeof rename.mutate>[0]["body"],
  ) => {
    setRowError(null);
    rename.mutate(
      { id, body },
      { onError: (e) => setRowError({ id, text: errorText(e) }) },
    );
  };

  const add = (e: React.FormEvent) => {
    e.preventDefault();
    const text = label.trim();
    if (text === "" || full) return;
    setAddError(null);
    create.mutate(
      { custom_label: text, client_id: crypto.randomUUID() },
      {
        onSuccess: () => setLabel(""),
        onError: (err) => setAddError(errorText(err)),
      },
    );
  };

  const target = items.find((s) => s.id === removing);
  return (
    <div className="space-y-4" data-testid="meals-screen">
      <SectionHeader as="h1" title={t("diary.slots.manage")} />
      <ul className={cn(cardClass, "divide-y divide-border-default")}>
        {items.map((s, i) => (
          <MealSlotRow
            key={s.id}
            slot={s}
            index={i}
            count={items.length}
            busy={busy}
            canRemove={items.length > 1}
            error={rowError?.id === s.id ? rowError.text : null}
            onRename={(text) => patch(s.id, { custom_label: text })}
            onResetName={() => patch(s.id, { clear_custom_label: true })}
            onMove={(d) => move(i, i + d)}
            onRemove={() => setRemoving(s.id)}
            dragProps={{
              onDragStart: () => setDragId(s.id),
              onDragOver: (e) => e.preventDefault(),
              onDrop: (e) => {
                e.preventDefault();
                const from = items.findIndex((x) => x.id === dragId);
                setDragId(null);
                move(from, i);
              },
            }}
          />
        ))}
      </ul>
      <Card as="section" className="space-y-2">
        <form onSubmit={add} noValidate className="space-y-2">
          <label
            htmlFor="new-meal"
            className="text-md font-medium text-text-primary"
          >
            {t("diary.slots.add")}
          </label>
          <input
            id="new-meal"
            value={label}
            disabled={full}
            onChange={(e) => setLabel(clampLabel(e.target.value))}
            className={inputClass}
          />
          <p className={hintClass}>{t("diary.slots.name_hint")}</p>
          <p
            className={hintClass}
            data-testid="new-meal-counter"
            data-allow-digits
          >
            {[...label].length}/{MAX_LABEL}
          </p>
          {full ? (
            <p className={hintClass} data-testid="meal-limit">
              {t("diary.slots.limit", { max: MAX_SLOTS })}
            </p>
          ) : null}
          {addError ? (
            <p role="alert" className="text-sm text-text-primary">
              {addError}
            </p>
          ) : null}
          <Button
            type="submit"
            disabled={full || label.trim() === "" || create.isPending}
          >
            {t("diary.slots.add")}
          </Button>
        </form>
      </Card>
      <a
        href={`/${locale}/diary`}
        className={buttonClass({ variant: "outline" })}
      >
        {t("nav.diary")}
      </a>
      {target ? (
        <ConfirmDialog
          message={t("diary.slots.remove_note")}
          confirmLabel={t("diary.slots.remove")}
          cancelLabel={t("common.cancel")}
          busy={archive.isPending}
          onCancel={() => setRemoving(null)}
          onConfirm={() =>
            archive.mutate(target.id, {
              onError: (e) =>
                setRowError({ id: target.id, text: errorText(e) }),
              onSettled: () => setRemoving(null),
            })
          }
        />
      ) : null}
    </div>
  );
}
