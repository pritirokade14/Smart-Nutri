"use client";

import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { ApiError } from "@/lib/api/errors";
import { useSaveWeight } from "../hooks/useWeights";
import { formatWeight } from "../lib/format";

const num = (raw: string): number | null => {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
};

/**
 * Log or edit a weigh-in. The API decides whether a value is plausible: on
 * `weight_needs_confirm` the user is asked, then the same request is resent
 * with `confirm_unusual`. Under hidden numbers `previous` is null and the
 * hidden copy is used (no kg shown).
 */
export function WeighInDialog({
  today,
  existing,
  onClose,
}: {
  /** The account's local today, from the API (the default and the latest date). */
  today: string;
  /** Editing: the weigh-in's date is fixed and its kg prefilled (null when hidden). */
  existing?: { date: string; weight_kg: number | null };
  onClose: () => void;
}) {
  const t = useTranslations();
  const ids = { date: useId(), kg: useId() };
  const save = useSaveWeight();
  const [date, setDate] = useState(existing?.date ?? today);
  const [kg, setKg] = useState(
    existing?.weight_kg == null ? "" : String(existing.weight_kg),
  );
  const [invalid, setInvalid] = useState(false);
  const [confirm, setConfirm] = useState<{ previous: number | null } | null>(
    null,
  );
  const [error, setError] = useState<ApiError | null>(null);

  function send(confirmUnusual: boolean) {
    const value = num(kg);
    if (value === null || value <= 0 || date === "") {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    setError(null);
    save.mutate(
      {
        day: date,
        body: { weight_kg: value, confirm_unusual: confirmUnusual },
      },
      {
        onSuccess: onClose,
        onError: (e) => {
          if (e.code === "weight_needs_confirm") {
            const p = e.details.previous;
            setConfirm({ previous: typeof p === "number" ? p : null });
            return;
          }
          setConfirm(null);
          setError(e);
        },
      },
    );
  }

  const formId = `${ids.kg}-form`;
  const errorText = error
    ? error.code === "network"
      ? t("meals.online_only")
      : t(errorKey(t, error))
    : invalid
      ? t("error.weight_out_of_range")
      : null;
  return (
    <Dialog
      title={t(existing ? "weight.edit" : "weight.add")}
      onClose={onClose}
      testId="weigh-in-dialog"
      actions={
        <>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          {confirm ? (
            <Button
              data-testid="weight-save-anyway"
              disabled={save.isPending}
              onClick={() => send(true)}
            >
              {t("weight.save_anyway")}
            </Button>
          ) : (
            <Button type="submit" form={formId} disabled={save.isPending}>
              {t("meals.log.save")}
            </Button>
          )}
        </>
      }
    >
      <form
        id={formId}
        noValidate
        onSubmit={(e) => {
          e.preventDefault();
          send(false);
        }}
        className="space-y-4"
      >
        <div className="space-y-1">
          <label htmlFor={ids.date} className={labelClass}>
            {t("weight.date")}
          </label>
          <input
            id={ids.date}
            type="date"
            value={date}
            max={today}
            disabled={existing != null}
            onChange={(e) => {
              setDate(e.target.value);
              setConfirm(null);
            }}
            className={inputClass}
          />
        </div>
        <div className="space-y-1">
          <label htmlFor={ids.kg} className={labelClass}>
            {t("weight.title")}
          </label>
          <input
            id={ids.kg}
            inputMode="decimal"
            value={kg}
            onChange={(e) => {
              setKg(e.target.value);
              setConfirm(null);
            }}
            className={inputClass}
            aria-invalid={invalid || undefined}
          />
          <p className={hintClass}>{t("weight.tip_same_time")}</p>
        </div>
      </form>
      {confirm ? (
        <p
          role="status"
          data-testid="weight-confirm"
          className="rounded-md bg-surface-muted px-3 py-2 text-md text-text-primary"
        >
          {confirm.previous === null
            ? t("weight.confirm_unusual_hidden")
            : t("weight.confirm_unusual", {
                previous: formatWeight(confirm.previous),
              })}
        </p>
      ) : null}
      {errorText ? (
        <p
          role="alert"
          data-testid="weight-error"
          className="text-md text-text-primary"
        >
          {errorText}
        </p>
      ) : null}
    </Dialog>
  );
}
