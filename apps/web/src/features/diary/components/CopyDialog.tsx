"use client";

import { useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { addDays } from "@/features/meals/api/meals";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import type { MealSlotOut } from "../api/mealSlots";
import { useCopyMeals } from "../hooks/useDiaryDay";
import { slotLabel } from "../lib/slotLabel";

/** What is being copied. The dates are calendar dates the user sees or picks. */
export type CopyKind =
  /** The day before the shown date, whole day, into the shown date. */
  | { kind: "yesterday"; toDate: string }
  /** A picked day, whole day, into the shown date. */
  | { kind: "day"; toDate: string }
  /** One slot of the shown date, to a picked day and slot. */
  | { kind: "meal"; fromDate: string; fromSlotId: string };

/**
 * Copy yesterday, a day, or a meal (POST /v1/meals/copy). One client_id per
 * dialog: a retry from the same dialog (a lost response, a double tap) reuses
 * it, so the API creates the copies once. The toast is a count only, never an
 * amount. Online-only: an offline failure shows meals.online_only.
 */
export function CopyDialog({
  target,
  today,
  slots,
  onClose,
  onCopied,
}: {
  target: CopyKind;
  today: string;
  slots?: readonly MealSlotOut[];
  onClose: () => void;
  /** Called with how many entries were created (or already existed). */
  onCopied: (count: number) => void;
}) {
  const t = useTranslations();
  const ids = { day: useId(), slot: useId() };
  const clientId = useRef(crypto.randomUUID());
  const copy = useCopyMeals();
  const [picked, setPicked] = useState(
    target.kind === "day" ? addDays(target.toDate, -1) : today,
  );
  const [slot, setSlot] = useState<string>(
    target.kind === "meal" ? target.fromSlotId : "",
  );

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const body =
      target.kind === "yesterday"
        ? {
            from_date: addDays(target.toDate, -1),
            to_date: target.toDate,
            client_id: clientId.current,
          }
        : target.kind === "day"
          ? {
              from_date: picked,
              to_date: target.toDate,
              client_id: clientId.current,
            }
          : {
              from_date: target.fromDate,
              from_slot_id: target.fromSlotId,
              to_date: picked,
              ...(slot ? { to_slot_id: slot } : {}),
              client_id: clientId.current,
            };
    copy.mutate(body, {
      onSuccess: (out) => {
        track("diary_entry_added", { method: "copy" });
        onCopied(out.created.length);
        onClose();
      },
    });
  }

  const title =
    target.kind === "yesterday"
      ? t("diary.copy_yesterday")
      : target.kind === "day"
        ? t("diary.copy_day")
        : t("diary.copy_meal");
  const error = copy.error as ApiError | null;
  const formId = `${ids.day}-form`;
  return (
    <Dialog
      title={title}
      onClose={onClose}
      testId="copy-dialog"
      actions={
        <>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" form={formId} disabled={copy.isPending}>
            {title}
          </Button>
        </>
      }
    >
      <form id={formId} noValidate onSubmit={submit} className="space-y-4">
        {target.kind !== "yesterday" ? (
          <div className="space-y-1">
            <label htmlFor={ids.day} className={labelClass}>
              {t("diary.copy_pick_day")}
            </label>
            <input
              id={ids.day}
              type="date"
              value={picked}
              max={today}
              onChange={(e) => e.target.value && setPicked(e.target.value)}
              className={inputClass}
            />
          </div>
        ) : null}
        {target.kind === "meal" && slots && slots.length > 0 ? (
          <div className="space-y-1">
            <label htmlFor={ids.slot} className={labelClass}>
              {t("diary.copy_pick_meal")}
            </label>
            <select
              id={ids.slot}
              value={slot}
              onChange={(e) => setSlot(e.target.value)}
              className={inputClass}
            >
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
        <p className={hintClass}>{t("meals.online_only")}</p>
      </form>
      {error ? (
        <p role="alert" className="text-md text-text-primary">
          {error.code === "network"
            ? t("meals.online_only")
            : t(errorKey(t, error))}
        </p>
      ) : null}
    </Dialog>
  );
}
