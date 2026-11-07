"use client";

import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog, Dialog } from "@/components/ui/Dialog";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { InfoIcon } from "@/components/ui/icons";
import type { UnitCode } from "@/features/foods/api/foods";
import { amountHint, unitLabel } from "@/features/foods/lib/unitLabel";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/cn";
import type { MealOut, MealPatch, QuickIn } from "../api/diary";
import type { MealSlotOut } from "../api/mealSlots";
import { useDeleteMeal, useUpdateMeal } from "../hooks/useDiaryDay";
import { slotLabel } from "../lib/slotLabel";

const MAX_GRAMS = 5000;

const num = (raw: string): number | null => {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
};

const show = (n: number | null | undefined): string =>
  n == null ? "" : String(n);

const QUICK_FIELDS = [
  ["energy_kcal", "diary.quick_add.energy"],
  ["protein_g", "diary.quick_add.protein"],
  ["fat_g", "diary.quick_add.fat"],
  ["carbs_g", "diary.quick_add.carbs"],
  ["fibre_g", "diary.quick_add.fibre"],
] as const;

/**
 * Edit or remove one diary entry (web is online-only: both need a
 * connection, and a failed request shows meals.online_only). Only the fields
 * the user changed are sent; every other field is null (= unchanged).
 */
export function EditEntryDialog({
  entry,
  slots,
  onClose,
}: {
  entry: MealOut;
  /** The member's slots; the move control is hidden until they load. */
  slots?: readonly MealSlotOut[];
  onClose: () => void;
}) {
  const t = useTranslations();
  const ids = { grams: useId(), slot: useId(), name: useId() };
  const update = useUpdateMeal();
  const remove = useDeleteMeal();
  const quick = entry.source_kind === "quick_add";
  // Hidden numbers arrive as null: the quick values cannot be edited blind.
  const quickEditable = quick && entry.nutrients.energy_kcal !== null;
  // A food logged by unit is edited by unit; an older row, by grams.
  const units = entry.portion_units ?? [];
  const byUnit = !quick && entry.unit != null && units.length > 0;
  const [unitCode, setUnitCode] = useState(entry.unit ?? "");
  const [quantity, setQuantity] = useState(show(entry.quantity));
  const [grams, setGrams] = useState(show(entry.grams));
  const [slot, setSlot] = useState(entry.meal_slot_id);
  const [name, setName] = useState(entry.product_name);
  const [q, setQ] = useState<Record<string, string>>({
    energy_kcal: show(entry.nutrients.energy_kcal),
    protein_g: show(entry.nutrients.protein_g),
    fat_g: show(entry.nutrients.fat_g),
    carbs_g: show(entry.nutrients.carbs_g),
    fibre_g: show(entry.nutrients.fibre_g),
  });
  const [invalid, setInvalid] = useState(false);
  const [asking, setAsking] = useState(false);

  const tt = (k: string, v?: Record<string, string | number>) =>
    t(k as never, v as never);
  const errorText = (e: ApiError) =>
    e.code === "network" ? t("meals.online_only") : t(errorKey(t, e));

  function save(e: React.FormEvent) {
    e.preventDefault();
    const patch: MealPatch = {};
    if (byUnit) {
      const n = num(quantity);
      if (n === null || n <= 0) {
        setInvalid(true);
        return;
      }
      if (n !== entry.quantity || unitCode !== entry.unit) {
        patch.quantity = n;
        patch.unit = unitCode as UnitCode;
      }
    } else if (!quick && entry.grams != null) {
      const g = num(grams);
      if (g === null || g <= 0 || g > MAX_GRAMS) {
        setInvalid(true);
        return;
      }
      if (g !== entry.grams) patch.grams = g;
    }
    if (quickEditable) {
      const energy = num(q.energy_kcal);
      if (energy === null || energy <= 0) {
        setInvalid(true);
        return;
      }
      const quickIn: QuickIn = {
        name: name.trim() === "" ? null : name.trim(),
        energy_kcal: energy,
        protein_g: num(q.protein_g),
        fat_g: num(q.fat_g),
        carbs_g: num(q.carbs_g),
        fibre_g: num(q.fibre_g),
      };
      const changed =
        name.trim() !== entry.product_name.trim() ||
        QUICK_FIELDS.some(([k]) => num(q[k]) !== (entry.nutrients[k] ?? null));
      if (changed) patch.quick = quickIn;
    }
    if (slot !== entry.meal_slot_id) patch.meal_slot_id = slot;
    setInvalid(false);
    if (Object.keys(patch).length === 0) {
      onClose();
      return;
    }
    update.mutate({ id: entry.id, patch }, { onSuccess: onClose });
  }

  const error = update.error ?? remove.error;
  const formId = `${ids.grams}-form`;
  const title =
    entry.product_name.trim() === ""
      ? t("diary.quick_add_name")
      : entry.product_name;
  return (
    <>
      <Dialog
        title={t("diary.edit")}
        onClose={onClose}
        testId="edit-entry-dialog"
        actions={
          <>
            <Button
              variant="ghost"
              onClick={() => setAsking(true)}
              disabled={remove.isPending}
            >
              {t("diary.delete")}
            </Button>
            <Button variant="outline" onClick={onClose}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" form={formId} disabled={update.isPending}>
              {t("meals.log.save")}
            </Button>
          </>
        }
      >
        <p className="text-md font-medium break-words text-text-primary">
          {title}
        </p>
        <p className="flex items-start gap-2 rounded-md bg-surface-muted px-3 py-2 text-sm text-text-secondary">
          <InfoIcon className="mt-0.5 size-4 shrink-0" />
          <span>{t("meals.online_only")}</span>
        </p>
        <form id={formId} noValidate onSubmit={save} className="space-y-4">
          {byUnit ? (
            <div className="space-y-2" data-testid="edit-portion">
              <fieldset className="m-0 flex min-w-0 flex-wrap gap-2 border-0 p-0">
                <legend className="sr-only">{t("foods.portion.title")}</legend>
                {units.map((u) => (
                  <button
                    key={u.code}
                    type="button"
                    data-testid={`edit-unit-${u.code}`}
                    aria-pressed={u.code === unitCode}
                    onClick={() => setUnitCode(u.code)}
                    className={cn(
                      "min-h-9 cursor-pointer rounded-full border px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
                      u.code === unitCode
                        ? "border-brand-primary bg-brand-soft text-brand-primary"
                        : "border-border-default bg-surface-default text-text-primary hover:bg-surface-muted",
                    )}
                  >
                    {unitLabel(tt, u.code, num(quantity) ?? 1)}
                  </button>
                ))}
              </fieldset>
              <label htmlFor={ids.grams} className={labelClass}>
                {t("foods.portion.quantity")}
              </label>
              <input
                id={ids.grams}
                inputMode="decimal"
                value={quantity}
                aria-invalid={invalid || undefined}
                onChange={(e) => setQuantity(e.target.value)}
                data-allow-digits
                className={inputClass}
              />
              {units.find((u) => u.code === unitCode) ? (
                <p className={hintClass} data-allow-digits>
                  {amountHint(
                    tt,
                    units.find(
                      (u) => u.code === unitCode,
                    ) as (typeof units)[number],
                    entry.basis,
                  )}
                </p>
              ) : null}
            </div>
          ) : !quick && entry.grams != null ? (
            <div className="space-y-1">
              <label htmlFor={ids.grams} className={labelClass}>
                {t("meals.log.amount_grams")}
              </label>
              <input
                id={ids.grams}
                inputMode="decimal"
                value={grams}
                aria-invalid={invalid || undefined}
                onChange={(e) => setGrams(e.target.value)}
                className={inputClass}
              />
              {invalid ? (
                <p className={hintClass}>
                  {t("meals.log.amount_invalid", { max: String(MAX_GRAMS) })}
                </p>
              ) : null}
            </div>
          ) : null}
          {quickEditable ? (
            <>
              <div className="space-y-1">
                <label htmlFor={ids.name} className={labelClass}>
                  {t("diary.quick_add.name_label")}
                </label>
                <input
                  id={ids.name}
                  value={name}
                  maxLength={60}
                  onChange={(e) => setName(e.target.value)}
                  className={inputClass}
                />
              </div>
              {QUICK_FIELDS.map(([k, label]) => (
                <div key={k} className="space-y-1">
                  <label htmlFor={`${ids.name}-${k}`} className={labelClass}>
                    {t(label)}
                  </label>
                  <input
                    id={`${ids.name}-${k}`}
                    inputMode="decimal"
                    value={q[k]}
                    aria-invalid={(invalid && k === "energy_kcal") || undefined}
                    onChange={(e) =>
                      setQ((v) => ({ ...v, [k]: e.target.value }))
                    }
                    className={inputClass}
                  />
                </div>
              ))}
              <p className={hintClass}>{t("foods.blank_is_unknown")}</p>
            </>
          ) : null}
          {slots && slots.length > 0 ? (
            <div className="space-y-1">
              <label htmlFor={ids.slot} className={labelClass}>
                {t("diary.move")}
              </label>
              <select
                id={ids.slot}
                value={slot}
                onChange={(e) => setSlot(e.target.value)}
                className={inputClass}
              >
                {slots.some((s) => s.id === entry.meal_slot_id) ? null : (
                  <option value={entry.meal_slot_id} disabled>
                    {t("diary.slots.removed")}
                  </option>
                )}
                {slots.map((s) => (
                  <option key={s.id} value={s.id}>
                    {slotLabel((k) => t(k), {
                      labelKey: s.label_key,
                      customLabel: s.custom_label,
                    })}
                  </option>
                ))}
              </select>
            </div>
          ) : null}
        </form>
        {error ? (
          <p role="alert" className="text-md text-text-primary">
            {errorText(error)}
          </p>
        ) : null}
      </Dialog>
      {asking ? (
        <ConfirmDialog
          message={t("diary.delete_confirm")}
          confirmLabel={t("diary.delete")}
          cancelLabel={t("common.cancel")}
          busy={remove.isPending}
          onCancel={() => setAsking(false)}
          onConfirm={() =>
            remove.mutate(entry.id, {
              onSuccess: () => {
                track("meal_removed");
                setAsking(false);
                onClose();
              },
              onError: () => setAsking(false),
            })
          }
        />
      ) : null}
    </>
  );
}
