"use client";

import { useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { InfoIcon } from "@/components/ui/icons";
import { SlotChips } from "@/features/diary/components/AddFoodPanel";
import { useMealSlots } from "@/features/diary/hooks/useMealSlots";
import {
  clearDiaryAddContext,
  type DiaryAddContext,
  getDiaryAddContext,
} from "@/features/diary/lib/addContext";
import { formatAmount } from "@/features/history/lib/summary";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import type { MealIn, MealOut } from "../api/meals";
import { useDeleteMeal, useLogMeal } from "../hooks/useMeals";

export type LogMealProduct = {
  /** Our own product (exactly one of productId and barcode is sent). */
  productId: string | null;
  /** Open Food Facts barcode, used when there is no productId. */
  barcode: string | null;
  name: string;
  /** Grams in one serving from the label; null hides "servings". */
  servingSizeG: number | null;
};

export type LogMealMember = {
  id: string;
  name: string;
  isPrimary: boolean;
  relation?: string;
};

type Mode = "servings" | "grams";

// The API's bounds (MealIn: 0 < grams <= 5000, 0 < servings <= 200).
const MAX: Record<Mode, number> = { servings: 200, grams: 5000 };

function parseAmount(raw: string, mode: Mode): number | null {
  const n = Number(raw.trim().replace(",", "."));
  return raw.trim() !== "" && Number.isFinite(n) && n > 0 && n <= MAX[mode]
    ? n
    : null;
}

/** A datetime-local value as a timezone-aware ISO string (or null for "now"). */
function toAware(local: string): string | null {
  if (!local) return null;
  const d = new Date(local);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

function localInputValue(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * "I ate this": log a portion for one family member (POST /v1/meals).
 *
 * Web logging is online-only (meals.online_only is always shown). One
 * client_id is used for the whole attempt series: a retry after an error
 * (including a timeout whose request may have reached the server) sends the
 * same id, so the API returns the stored row instead of a duplicate. The
 * success state shows the amount the API stored.
 */
export function LogMealDialog({
  product,
  members,
  memberId,
  localDate,
  onClose,
}: {
  product: LogMealProduct;
  members: readonly LogMealMember[];
  memberId: string;
  /** Logs onto this (past) day instead of "now"; set by the diary. */
  localDate?: string;
  onClose: () => void;
}) {
  const t = useTranslations();
  const ids = { member: useId(), amount: useId(), when: useId() };
  const hasServing = product.servingSizeG != null && product.servingSizeG > 0;
  const [member, setMember] = useState(memberId);
  const [mode, setMode] = useState<Mode>(hasServing ? "servings" : "grams");
  const [amount, setAmount] = useState<Record<Mode, string>>({
    servings: "1",
    grams: "",
  });
  const [when, setWhen] = useState("");
  const [invalid, setInvalid] = useState(false);
  const [saved, setSaved] = useState<MealOut | null>(null);
  const [undone, setUndone] = useState(false);
  const clientId = useRef<string | null>(null);
  const log = useLogMeal();
  const undo = useDeleteMeal();
  // The slot comes from the server's list and suggestion (never worked out
  // here); until the list loads, no chips show and no slot is sent.
  const slots = useMealSlots();
  // From the Diary's add-food flow: its day and slot (else the API picks).
  const [ctx] = useState<DiaryAddContext | null>(() =>
    typeof window === "undefined" ? null : getDiaryAddContext(),
  );
  const logDate = localDate ?? ctx?.localDate ?? undefined;
  const [pickedSlot, setPickedSlot] = useState<string | null>(null);
  const slotId =
    pickedSlot ?? ctx?.slotId ?? slots.data?.suggested_slot_id ?? null;

  const who = (id: string) => {
    const m = members.find((x) => x.id === id);
    if (!m) return "";
    if (m.name.trim() !== "") return m.name;
    if (m.isPrimary) return t("result.you");
    return t(`share.relation.${m.relation ?? "other"}`);
  };
  const savedFor = (id: string) =>
    members.find((x) => x.id === id)?.isPrimary
      ? t("meals.log.saved_you")
      : t("meals.log.saved", { who: who(id) });

  const errorText = (e: ApiError | null) => {
    if (!e) return null;
    const key = `error.${e.code}`;
    return t.has(key) ? t(key) : t("error.internal_error");
  };

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const n = parseAmount(amount[mode], mode);
    if (n === null) {
      setInvalid(true);
      return;
    }
    setInvalid(false);
    clientId.current ??= crypto.randomUUID();
    // A past day sends local_date; local_date and eaten_at never go together.
    const eatenAt = logDate ? null : toAware(when);
    const body: MealIn = {
      member_id: member,
      ...(product.productId
        ? { product_id: product.productId }
        : { barcode: product.barcode }),
      ...(mode === "servings" ? { servings: n } : { grams: n }),
      ...(eatenAt ? { eaten_at: eatenAt } : {}),
      ...(logDate ? { local_date: logDate } : {}),
      ...(slots.data && slotId ? { meal_slot_id: slotId } : {}),
      client_id: clientId.current,
    };
    log.mutate(body, {
      onSuccess: (meal) => {
        clientId.current = null; // the next log is a new attempt series
        setSaved(meal);
        track("meal_logged");
        if (ctx) {
          // The method only: no product, member or portion.
          track("diary_entry_added", { method: ctx.method });
          clearDiaryAddContext();
        }
      },
    });
  }

  function undoLog() {
    if (!saved) return;
    undo.mutate(saved.id, {
      onSuccess: () => {
        setUndone(true);
        track("meal_log_undone");
      },
    });
  }

  const now = new Date();
  const notice = (
    <p className="flex items-start gap-2 rounded-md bg-surface-muted px-3 py-2 text-sm text-text-secondary">
      <InfoIcon className="mt-0.5 size-4 shrink-0" />
      <span>{t("meals.online_only")}</span>
    </p>
  );

  if (saved) {
    return (
      <Dialog
        title={t("meals.log.title")}
        onClose={onClose}
        testId="log-meal-dialog"
        actions={
          <>
            {!undone ? (
              <Button
                variant="outline"
                onClick={undoLog}
                disabled={undo.isPending}
              >
                {t("meals.log.undo")}
              </Button>
            ) : null}
            <Button onClick={onClose}>{t("common.close")}</Button>
          </>
        }
      >
        <div role="status" className="space-y-1">
          {undone ? (
            <p className="text-md text-text-primary">{t("meals.log.undone")}</p>
          ) : (
            <>
              <p className="text-md font-semibold text-text-primary">
                {savedFor(saved.member_id)}
              </p>
              <p className="text-md text-text-secondary">
                {saved.product_name}
              </p>
              {saved.grams != null ? (
                <p className="text-md text-text-secondary">
                  {t("history.item_amount", {
                    grams: formatAmount(saved.grams),
                  })}
                </p>
              ) : null}
            </>
          )}
        </div>
        {undo.isError ? (
          <p role="alert" className="text-md text-text-primary">
            {errorText(undo.error)}
          </p>
        ) : null}
      </Dialog>
    );
  }

  const formId = `${ids.member}-form`;
  return (
    <Dialog
      title={t("meals.log.title")}
      onClose={onClose}
      testId="log-meal-dialog"
      actions={
        <>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button type="submit" form={formId} disabled={log.isPending}>
            {t("meals.log.save")}
          </Button>
        </>
      }
    >
      <p className="text-md font-medium break-words text-text-primary">
        {product.name}
      </p>
      {notice}
      <form id={formId} noValidate onSubmit={submit} className="space-y-4">
        <div className="space-y-1">
          <label htmlFor={ids.member} className={labelClass}>
            {t("meals.log.member")}
          </label>
          <select
            id={ids.member}
            value={member}
            onChange={(e) => setMember(e.target.value)}
            className={inputClass}
          >
            {members.map((m) => (
              <option key={m.id} value={m.id}>
                {who(m.id)}
              </option>
            ))}
          </select>
        </div>

        {hasServing ? (
          <fieldset className="space-y-2">
            <legend className={labelClass}>{t("meals.log.portion")}</legend>
            <div className="flex flex-wrap gap-4">
              {(["servings", "grams"] as const).map((m) => (
                <label
                  key={m}
                  className="flex min-h-11 items-center gap-2 text-md"
                >
                  <input
                    type="radio"
                    name={`${ids.amount}-mode`}
                    checked={mode === m}
                    onChange={() => {
                      setMode(m);
                      setInvalid(false);
                    }}
                  />
                  {t(`meals.log.${m}`)}
                </label>
              ))}
            </div>
          </fieldset>
        ) : null}

        <div className="space-y-1">
          <label htmlFor={ids.amount} className={labelClass}>
            {mode === "servings"
              ? t("meals.log.amount_servings")
              : t("meals.log.amount_grams")}
          </label>
          <input
            id={ids.amount}
            inputMode="decimal"
            value={amount[mode]}
            aria-invalid={invalid || undefined}
            aria-describedby={`${ids.amount}-hint`}
            onChange={(e) =>
              setAmount((a) => ({ ...a, [mode]: e.target.value }))
            }
            className={inputClass}
          />
          <p id={`${ids.amount}-hint`} className={hintClass}>
            {invalid
              ? t("meals.log.amount_invalid", { max: String(MAX[mode]) })
              : mode === "servings" && product.servingSizeG != null
                ? t("meals.log.serving_size", {
                    grams: formatAmount(product.servingSizeG),
                  })
                : null}
          </p>
        </div>

        {slots.data && slotId ? (
          <SlotChips
            slots={slots.data.items}
            value={slotId}
            onChange={setPickedSlot}
          />
        ) : null}

        {logDate ? null : (
          <div className="space-y-1">
            <label htmlFor={ids.when} className={labelClass}>
              {t("meals.log.eaten_at")}
            </label>
            <input
              id={ids.when}
              type="datetime-local"
              value={when}
              max={localInputValue(now)}
              min={localInputValue(new Date(now.getTime() - 30 * 86_400_000))}
              onChange={(e) => setWhen(e.target.value)}
              className={inputClass}
            />
            {when === "" ? (
              <p className={hintClass}>{t("meals.log.now")}</p>
            ) : null}
          </div>
        )}
      </form>
      {log.isError ? (
        <p role="alert" className="text-md text-text-primary">
          {errorText(log.error)}
        </p>
      ) : null}
    </Dialog>
  );
}
