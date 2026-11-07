"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRef, useState } from "react";
import { Button, buttonClass } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { ErrorState } from "@/components/ui/ErrorState";
import { InfoIcon } from "@/components/ui/icons";
import { LoadingState } from "@/components/ui/Skeleton";
import type { FoodHit } from "@/features/foods/api/foods";
import { FoodSearch } from "@/features/foods/components/FoodSearch";
import { PortionPicker } from "@/features/foods/components/PortionPicker";
import { SourceCredit } from "@/features/foods/components/SourceCredit";
import { portionLine } from "@/features/foods/lib/portionLine";
import type { MealIn } from "@/features/meals/api/meals";
import { useLogMeal } from "@/features/meals/hooks/useMeals";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/cn";
import type { RecentItem } from "../api/diary";
import { useRecents } from "../hooks/useDiaryDay";
import { useMealSlots } from "../hooks/useMealSlots";
import { type DiaryAddMethod, setDiaryAddContext } from "../lib/addContext";
import { slotLabel } from "../lib/slotLabel";
import { QuickAddForm } from "./QuickAddForm";

type Segment = "recent" | "search" | "quick";

const recentCredits = (r: RecentItem): string[] =>
  r.attributions && r.attributions.length > 0
    ? r.attributions
    : r.attribution
      ? [r.attribution]
      : [];

/** Chips for the member's slots; hidden until the list loads. */
export function SlotChips({
  slots,
  value,
  onChange,
}: {
  slots: readonly {
    id: string;
    label_key: string | null;
    custom_label: string | null;
  }[];
  value: string;
  onChange: (id: string) => void;
}) {
  const t = useTranslations();
  return (
    <fieldset
      data-testid="slot-chips"
      className="m-0 flex min-w-0 flex-wrap gap-2 border-0 p-0"
    >
      <legend className="sr-only">{t("diary.copy_pick_meal")}</legend>
      {slots.map((s) => {
        const on = s.id === value;
        return (
          <button
            key={s.id}
            type="button"
            aria-pressed={on}
            onClick={() => onChange(s.id)}
            className={cn(
              "min-h-9 cursor-pointer rounded-full border px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
              on
                ? "border-brand-primary bg-brand-soft text-brand-primary"
                : "border-border-default bg-surface-default text-text-primary hover:bg-surface-muted",
            )}
          >
            {slotLabel((k) => t(k), {
              labelKey: s.label_key,
              customLabel: s.custom_label,
            })}
          </button>
        );
      })}
    </fieldset>
  );
}

/**
 * The add-food panel (a dialog on desktop, a bottom sheet on a phone):
 * Recent (one tap logs the last portion), Search, Barcode and Label scan (the
 * existing flows), and Quick add. The slot is preselected (the tapped slot,
 * else the server's `suggested_slot_id`: the client never works out a slot).
 * A day other than today sends `local_date`. Web is online-only.
 */
export function AddFoodPanel({
  date,
  today,
  slotId,
  onClose,
  onLogged,
}: {
  date: string;
  today: string;
  /** The tapped slot; omitted: the server's suggestion. */
  slotId?: string;
  onClose: () => void;
  /** Called after a successful log (the panel closes too). */
  onLogged: () => void;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const slots = useMealSlots();
  const [picked, setPicked] = useState<string | null>(null);
  const [segment, setSegment] = useState<Segment>("recent");
  const [hit, setHit] = useState<FoodHit | null>(null);
  const [viaBarcode, setViaBarcode] = useState(false);
  const chosen = picked ?? slotId ?? slots.data?.suggested_slot_id ?? null;
  const loaded = slots.data !== undefined && chosen !== null;
  const recents = useRecents(loaded ? (chosen ?? undefined) : undefined);
  const log = useLogMeal();
  const clientId = useRef<string | null>(null);
  const localDate = date === today ? undefined : date;

  function logRecent(item: RecentItem) {
    clientId.current ??= crypto.randomUUID();
    log.mutate(
      {
        ...(item.food_id
          ? { food_id: item.food_id }
          : item.custom_food_id
            ? { custom_food_id: item.custom_food_id }
            : item.recipe_id
              ? { recipe_id: item.recipe_id }
              : item.product_id
                ? { product_id: item.product_id }
                : { barcode: item.barcode }),
        // The last portion as it was logged: its unit, else grams (a legacy row).
        ...(item.quantity != null && item.unit
          ? {
              quantity: item.quantity,
              unit: item.unit as NonNullable<MealIn["unit"]>,
            }
          : item.basis === "ml"
            ? // An ml food with no saved unit: millilitres, never grams.
              { quantity: item.grams, unit: "ml" as const }
            : { grams: item.grams }),
        ...(loaded && chosen ? { meal_slot_id: chosen } : {}),
        ...(localDate ? { local_date: localDate } : {}),
        client_id: clientId.current,
      },
      {
        onSuccess: () => {
          clientId.current = null;
          track("diary_entry_added", { method: "recent" });
          onLogged();
        },
      },
    );
  }

  // Search, barcode and label are other pages: carry the day and slot there.
  const leave = (method: DiaryAddMethod) =>
    setDiaryAddContext({
      method,
      slotId: loaded ? chosen : null,
      localDate: localDate ?? null,
    });

  const logError = log.error as ApiError | null;
  const done = () => {
    onLogged();
  };

  return (
    <Dialog
      title={t("diary.add")}
      onClose={onClose}
      testId="add-food-panel"
      actions={
        <Button variant="outline" onClick={onClose}>
          {t("common.close")}
        </Button>
      }
    >
      <p className="flex items-start gap-2 rounded-md bg-surface-muted px-3 py-2 text-sm text-text-secondary">
        <InfoIcon className="mt-0.5 size-4 shrink-0" />
        <span>{t("meals.online_only")}</span>
      </p>
      {slots.data && chosen ? (
        <SlotChips
          slots={slots.data.items}
          value={chosen}
          onChange={setPicked}
        />
      ) : null}
      <div className="flex flex-wrap gap-2" role="tablist">
        {(["recent", "search", "quick"] as const).map((s) => (
          <button
            key={s}
            type="button"
            role="tab"
            aria-selected={segment === s}
            onClick={() => setSegment(s)}
            className={cn(
              "min-h-9 cursor-pointer rounded-full px-4 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
              segment === s
                ? "bg-brand-primary text-brand-on"
                : "bg-surface-muted text-text-primary",
            )}
          >
            {s === "recent"
              ? t("foods.recent")
              : s === "search"
                ? t("search.title")
                : t("foods.quick_add")}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2" data-testid="add-food-links">
        <a
          href={`/${locale}/scan`}
          onClick={() => leave("barcode")}
          className={buttonClass({ variant: "outline", size: "sm" })}
        >
          {t("scan.title")}
        </a>
        <a
          href={`/${locale}/diary/foods/new`}
          data-testid="new-food-link"
          className={buttonClass({ variant: "outline", size: "sm" })}
        >
          {t("foods.new_food")}
        </a>
        <a
          href={`/${locale}/diary/recipes/new`}
          data-testid="new-recipe-link"
          className={buttonClass({ variant: "outline", size: "sm" })}
        >
          {t("foods.new_recipe")}
        </a>
        <a
          href={`/${locale}/scan/label`}
          onClick={() => leave("label")}
          className={buttonClass({ variant: "outline", size: "sm" })}
        >
          {t("label.title")}
        </a>
      </div>
      {segment === "search" ? (
        hit ? (
          <PortionPicker
            hit={hit}
            slotId={loaded ? chosen : null}
            localDate={localDate}
            onLogged={done}
            onCancel={() => setHit(null)}
            method={viaBarcode ? "barcode" : undefined}
          />
        ) : (
          <FoodSearch
            onPick={(h, barcode) => {
              setViaBarcode(barcode === true);
              setHit(h);
            }}
            onBarcodeProduct={(code) => {
              leave("barcode");
              window.location.assign(`/${locale}/result/${code}`);
            }}
          />
        )
      ) : segment === "quick" ? (
        <QuickAddForm
          slotId={loaded ? chosen : null}
          localDate={localDate}
          onLogged={done}
        />
      ) : recents.isPending && loaded ? (
        <LoadingState label={t("common.loading")} lines={2} />
      ) : recents.isError ? (
        <ErrorState
          message={t(errorKey(t, recents.error))}
          onRetry={() => void recents.refetch()}
          retrying={recents.isFetching}
        />
      ) : (
        <ul className="divide-y divide-border-default" data-testid="recents">
          {(recents.data?.items ?? []).map((r) => (
            <li
              key={`${r.food_id ?? r.custom_food_id ?? r.recipe_id ?? r.product_id ?? r.barcode}`}
            >
              <button
                type="button"
                data-testid="recent-item"
                disabled={log.isPending}
                onClick={() => logRecent(r)}
                className="flex min-h-11 w-full cursor-pointer items-center justify-between gap-2 py-2 text-left hover:bg-surface-muted"
              >
                <span className="min-w-0 text-md font-medium break-words text-text-primary">
                  {r.name}
                  <SourceCredit keys={recentCredits(r)} />
                </span>
                <span className="shrink-0 text-sm text-text-secondary">
                  {portionLine((k, v) => t(k as never, v as never), {
                    quantity: r.quantity,
                    unit: r.unit,
                    grams: r.grams,
                    basis: r.basis,
                    unitSource: r.unit_source,
                  })}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {logError ? (
        <p role="alert" className="text-md text-text-primary">
          {logError.code === "network"
            ? t("meals.online_only")
            : t(errorKey(t, logError))}
        </p>
      ) : null}
    </Dialog>
  );
}
