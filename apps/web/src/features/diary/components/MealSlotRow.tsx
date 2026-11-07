"use client";

import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { hintClass, inputClass } from "@/components/ui/field";
import type { MealSlotOut } from "../api/mealSlots";
import { slotLabel } from "../lib/slotLabel";

export const MAX_LABEL = 30;

/** At most 30 code points (not UTF-16 units: Devanagari counts per character). */
export const clampLabel = (v: string): string =>
  [...v].slice(0, MAX_LABEL).join("");

/**
 * One meal on the Meals screen: its name (the user's own text exactly as
 * typed, or the translated default), an inline rename, up and down buttons
 * (the keyboard path; rows also drag) and Remove. No numbers here.
 */
export function MealSlotRow({
  slot,
  index,
  count,
  busy,
  canRemove,
  error,
  onRename,
  onResetName,
  onMove,
  onSetWindow,
  onRemove,
  dragProps,
}: {
  slot: MealSlotOut;
  index: number;
  count: number;
  busy: boolean;
  canRemove: boolean;
  error?: string | null;
  onRename: (label: string) => void;
  onResetName: () => void;
  onMove: (delta: -1 | 1) => void;
  onSetWindow: (w: { start: string; end: string } | null) => void;
  onRemove: () => void;
  dragProps?: React.HTMLAttributes<HTMLLIElement>;
}) {
  const t = useTranslations();
  const inputId = useId();
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState("");
  const title = slotLabel((k) => t(k), {
    labelKey: slot.label_key,
    customLabel: slot.custom_label,
  });
  const hhmm = (v: string | undefined) => (v ?? "").slice(0, 5);
  const win = slot.default_time_window;
  const [start, setStart] = useState(hhmm(win?.start));
  const [end, setEnd] = useState(hhmm(win?.end));
  const windowValid =
    (start === "" && end === "") || (start !== "" && end !== "");
  const used = [...value].length;
  const trimmed = value.trim();
  return (
    <li
      data-testid="meal-slot-row"
      data-slot-id={slot.id}
      draggable={!editing}
      className="space-y-2 px-4 py-3"
      {...dragProps}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span
          data-testid="meal-slot-name"
          className="min-w-0 text-md font-semibold break-words text-text-primary"
        >
          {title}
        </span>
        <span className="flex flex-wrap items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            aria-label={t("diary.slots.move_up", { title })}
            data-testid="meal-slot-up"
            disabled={busy || index === 0}
            onClick={() => onMove(-1)}
          >
            <span aria-hidden="true">↑</span>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            aria-label={t("diary.slots.move_down", { title })}
            data-testid="meal-slot-down"
            disabled={busy || index === count - 1}
            onClick={() => onMove(1)}
          >
            <span aria-hidden="true">↓</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            aria-label={`${t("diary.slots.rename")}: ${title}`}
            disabled={busy || editing}
            onClick={() => {
              setValue(slot.custom_label ?? "");
              setEditing(true);
            }}
          >
            {t("diary.slots.rename")}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            aria-label={`${t("diary.slots.remove")}: ${title}`}
            data-testid="meal-slot-remove"
            disabled={busy || !canRemove}
            onClick={onRemove}
          >
            {t("diary.slots.remove")}
          </Button>
        </span>
      </div>
      {!canRemove ? (
        <p className={hintClass}>{t("diary.slots.last_active")}</p>
      ) : null}
      {editing ? (
        <form
          className="space-y-2"
          noValidate
          onSubmit={(e) => {
            e.preventDefault();
            if (trimmed === "") return;
            onRename(trimmed);
            setEditing(false);
          }}
        >
          <label htmlFor={inputId} className="sr-only">
            {t("diary.slots.rename")}
          </label>
          <input
            id={inputId}
            value={value}
            onChange={(e) => setValue(clampLabel(e.target.value))}
            className={inputClass}
          />
          <p className={hintClass}>{t("diary.slots.name_hint")}</p>
          <p
            className={hintClass}
            data-testid="meal-slot-counter"
            data-allow-digits
          >
            {used}/{MAX_LABEL}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button type="submit" size="sm" disabled={trimmed === ""}>
              {t("members.form.save")}
            </Button>
            {slot.is_default && slot.custom_label ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  onResetName();
                  setEditing(false);
                }}
              >
                {t("diary.slots.reset_name")}
              </Button>
            ) : null}
            <Button variant="ghost" size="sm" onClick={() => setEditing(false)}>
              {t("common.cancel")}
            </Button>
          </div>
        </form>
      ) : null}
      <form
        className="space-y-2"
        noValidate
        data-testid="meal-slot-window"
        onSubmit={(e) => {
          e.preventDefault();
          if (!windowValid) return;
          onSetWindow(start === "" ? null : { start, end });
        }}
      >
        <fieldset className="space-y-1" disabled={busy}>
          <legend className="text-sm text-text-secondary">
            {t("diary.slots.time_window")}
          </legend>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="time"
              aria-label={t("diary.slots.time_start")}
              data-testid="meal-slot-start"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              className={inputClass}
            />
            <span aria-hidden="true">–</span>
            <input
              type="time"
              aria-label={t("diary.slots.time_end")}
              data-testid="meal-slot-end"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              className={inputClass}
            />
            <Button
              type="submit"
              variant="outline"
              size="sm"
              disabled={busy || !windowValid}
            >
              {t("members.form.save")}
            </Button>
          </div>
          <p className={hintClass}>{t("diary.slots.time_window_hint")}</p>
        </fieldset>
      </form>
      {error ? (
        <p role="alert" className="text-sm text-text-primary">
          {error}
        </p>
      ) : null}
    </li>
  );
}
