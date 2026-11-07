"use client";

import { useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { ApiError } from "@/lib/api/errors";
import { useAddFavouriteMeal } from "../hooks/useFavourites";

const MAX = 40;

/**
 * Save one slot of one day as a named favourite meal. The name is user text:
 * sent exactly as typed (no trim, no translation), 1 to 40 code points, and
 * never put in analytics. One client_id per dialog: a retry reuses it.
 */
export function SaveMealFavouriteDialog({
  fromDate,
  fromSlotId,
  onClose,
  onSaved,
}: {
  fromDate: string;
  fromSlotId: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const t = useTranslations();
  const nameId = useId();
  const clientId = useRef(crypto.randomUUID());
  const save = useAddFavouriteMeal();
  const [name, setName] = useState("");
  const length = [...name].length;
  const valid = name.trim() !== "" && length <= MAX;

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!valid) return;
    save.mutate(
      {
        from_date: fromDate,
        from_slot_id: fromSlotId,
        name,
        client_id: clientId.current,
      },
      {
        onSuccess: () => {
          onSaved();
          onClose();
        },
      },
    );
  }

  const error = save.error as ApiError | null;
  const formId = `${nameId}-form`;
  return (
    <Dialog
      title={t("favourites.save_meal")}
      onClose={onClose}
      testId="save-meal-dialog"
      actions={
        <>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button
            type="submit"
            form={formId}
            disabled={!valid || save.isPending}
          >
            {t("favourites.save_meal")}
          </Button>
        </>
      }
    >
      <form id={formId} noValidate onSubmit={submit} className="space-y-2">
        <label htmlFor={nameId} className={labelClass}>
          {t("favourites.meal_name")}
        </label>
        <input
          id={nameId}
          value={name}
          autoComplete="off"
          onChange={(e) => setName(e.target.value)}
          aria-invalid={(name !== "" && !valid) || undefined}
          className={inputClass}
        />
        <p className={hintClass}>{t("favourites.meal_name_hint")}</p>
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
