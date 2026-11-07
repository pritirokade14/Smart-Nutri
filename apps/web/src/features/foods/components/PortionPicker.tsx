"use client";

import { useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { chipClass } from "@/components/ui/Chip";
import { ErrorState } from "@/components/ui/ErrorState";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { LoadingState } from "@/components/ui/Skeleton";
import { useLogMeal } from "@/features/meals/hooks/useMeals";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/cn";
import type {
  FoodDetailOut,
  FoodHit,
  FoodUnitOut,
  UnitCode,
} from "../api/foods";
import { useDeletePortion, useFood, usePutPortion } from "../hooks/useFoods";
import { previewPortion } from "../lib/preview";
import { amountHint, unitChipLabel, unitLabel } from "../lib/unitLabel";
import { SourceCredit } from "./SourceCredit";

const FRACTIONS = [
  { value: "0.25", label: "¼" },
  { value: "0.5", label: "½" },
  { value: "1", label: "1" },
  { value: "1.5", label: "1½" },
  { value: "2", label: "2" },
] as const;

// Labels for the preview rows (existing catalogue keys), in display order.
const ROWS = [
  ["energy_kcal", "confirm.field.energy_kcal", "energy"],
  ["protein_g", "confirm.field.protein_g", "macros"],
  ["carbs_g", "confirm.field.carbs_g", "macros"],
  ["sugars_g", "confirm.field.sugars_g", "macros"],
  ["fat_g", "confirm.field.fat_g", "macros"],
  ["sat_fat_g", "confirm.field.sat_fat_g", "macros"],
  ["fibre_g", "confirm.field.fiber_g", "macros"],
  ["salt_g", "confirm.field.salt_g", "macros"],
] as const;

// Grams can be set for these kinds of measure only (never g, ml or serving).
const NOT_SETTABLE = new Set(["g", "ml", "serving"]);

const num = (raw: string): number | null => {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
};

/**
 * Choose how much: unit chips (only what the API says resolves), a quantity
 * with fraction chips, the grams (or ml) line always shown, and a live
 * preview. The preview is the one piece of arithmetic on the web; the saved
 * values come from the API. A hidden number is not shown at all; an unknown
 * one reads "Not known", never 0.
 */
export function PortionPicker({
  hit,
  slotId,
  localDate,
  onLogged,
  onCancel,
}: {
  hit: Pick<FoodHit, "kind" | "id" | "name" | "is_dish">;
  slotId: string | null;
  localDate?: string;
  onLogged: () => void;
  onCancel: () => void;
}) {
  const t = useTranslations();
  const food = useFood(hit.kind, hit.id);
  if (food.isPending)
    return <LoadingState label={t("common.loading")} lines={3} />;
  if (food.isError || !food.data)
    return (
      <PickerError
        error={food.error}
        onRetry={() => void food.refetch()}
        retrying={food.isFetching}
        onCancel={onCancel}
      />
    );
  return (
    <Loaded
      hit={hit}
      food={food.data}
      slotId={slotId}
      localDate={localDate}
      onLogged={onLogged}
      onCancel={onCancel}
    />
  );
}

function PickerError({
  error,
  onRetry,
  retrying,
  onCancel,
}: {
  error: ApiError | null;
  onRetry: () => void;
  retrying: boolean;
  onCancel: () => void;
}) {
  const t = useTranslations();
  return (
    <div className="space-y-3">
      <ErrorState
        message={t(error ? errorKey(t, error) : "error.internal_error")}
        onRetry={onRetry}
        retrying={retrying}
      />
      <Button variant="outline" onClick={onCancel}>
        {t("common.cancel")}
      </Button>
    </div>
  );
}

function Loaded({
  hit,
  food,
  slotId,
  localDate,
  onLogged,
  onCancel,
}: {
  hit: Pick<FoodHit, "kind" | "id" | "name" | "is_dish">;
  food: FoodDetailOut;
  slotId: string | null;
  localDate?: string;
  onLogged: () => void;
  onCancel: () => void;
}) {
  const t = useTranslations();
  const qtyId = useId();
  const gramsId = useId();
  const log = useLogMeal();
  const put = usePutPortion(hit.kind, hit.id);
  const reset = useDeletePortion(hit.kind, hit.id);
  const clientId = useRef<string | null>(null);
  const [picked, setPicked] = useState<string | null>(null);
  const [quantity, setQuantity] = useState("1");
  const [editing, setEditing] = useState<string | null>(null);
  const [gramsText, setGramsText] = useState("");

  const units = food.units;
  const code =
    units.find((u) => u.code === picked)?.code ??
    units.find((u) => u.code === food.default_unit)?.code ??
    units[0]?.code ??
    null;
  const unit: FoodUnitOut | undefined = units.find((u) => u.code === code);
  const q = num(quantity);
  const valid = q !== null && q > 0 && unit !== undefined;
  const preview =
    valid && unit ? previewPortion(food.per_100, q, unit.grams_per_unit) : null;
  const hidden = food.numbers_hidden;
  const rows = ROWS.filter(([, , group]) => !hidden[group]);
  const dish = food.dish;
  const settable = food.settable_units;

  function save() {
    if (!valid || !unit) return;
    clientId.current ??= crypto.randomUUID();
    log.mutate(
      {
        ...(hit.kind === "food"
          ? { food_id: hit.id }
          : hit.kind === "product"
            ? { product_id: hit.id }
            : { barcode: hit.id }),
        quantity: q,
        unit: unit.code as UnitCode,
        ...(slotId ? { meal_slot_id: slotId } : {}),
        ...(localDate ? { local_date: localDate } : {}),
        client_id: clientId.current,
      },
      {
        onSuccess: () => {
          clientId.current = null;
          track("diary_entry_added", { method: "search" });
          onLogged();
        },
      },
    );
  }

  function saveGrams(e: React.FormEvent) {
    e.preventDefault();
    const g = num(gramsText);
    if (editing === null || g === null || g <= 0 || g > 2000) return;
    const target = editing;
    put.mutate(
      { unit: target, gramsPerUnit: g },
      {
        onSuccess: () => {
          setPicked(target);
          setEditing(null);
        },
      },
    );
  }

  const logError = log.error as ApiError | null;
  const portionError = (put.error ?? reset.error) as ApiError | null;
  const errorText = (e: ApiError) =>
    e.code === "network" ? t("meals.online_only") : t(errorKey(t, e));
  const editable = unit && !NOT_SETTABLE.has(unit.code);

  return (
    <div className="space-y-4" data-testid="portion-picker">
      <div className="space-y-1">
        <h3 className="text-md font-semibold break-words text-text-primary">
          {hit.name}
        </h3>
        <p className="text-sm text-text-secondary">
          {t("foods.portion.title")}
        </p>
      </div>

      {units.length === 0 ? (
        <p className={hintClass} data-testid="no-units">
          {t("unit.unknown")}
        </p>
      ) : (
        <fieldset
          data-testid="unit-chips"
          className="m-0 flex min-w-0 flex-wrap gap-2 border-0 p-0"
        >
          <legend className="sr-only">{t("foods.portion.title")}</legend>
          {units.map((u) => (
            <button
              key={u.code}
              type="button"
              data-testid={`unit-${u.code}`}
              aria-pressed={u.code === code}
              onClick={() => setPicked(u.code)}
              data-allow-digits
              className={cn(
                "min-h-9 cursor-pointer rounded-full border px-3 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
                u.code === code
                  ? "border-brand-primary bg-brand-soft text-brand-primary"
                  : "border-border-default bg-surface-default text-text-primary hover:bg-surface-muted",
              )}
            >
              {unitChipLabel(
                (k, v) => t(k as never, v as never),
                u,
                q !== null && q > 0 ? q : 1,
              )}
            </button>
          ))}
        </fieldset>
      )}

      <div className="space-y-2">
        <label htmlFor={qtyId} className={labelClass}>
          {t("foods.portion.quantity")}
        </label>
        <input
          id={qtyId}
          inputMode="decimal"
          value={quantity}
          aria-invalid={!valid || undefined}
          onChange={(e) => setQuantity(e.target.value)}
          data-allow-digits
          className={inputClass}
        />
        <div className="flex flex-wrap gap-2" data-testid="fraction-chips">
          {FRACTIONS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setQuantity(f.value)}
              data-allow-digits
              className={cn(
                chipClass,
                "cursor-pointer hover:bg-surface-default",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {unit ? (
        <div className="space-y-1">
          <p
            data-testid="grams-hint"
            data-allow-digits
            className="text-md text-text-primary"
          >
            {amountHint((k, v) => t(k as never, v as never), unit, food.basis)}
            {unit.user_override ? (
              <span className={cn(chipClass, "ml-2")}>
                {t("unit.your_value")}
              </span>
            ) : null}
          </p>
          <div className="flex flex-wrap gap-2">
            {editable ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setEditing(unit.code);
                  setGramsText(String(unit.grams_per_unit));
                }}
              >
                {t("unit.edit_grams")}
              </Button>
            ) : null}
            {unit.user_override ? (
              <Button
                variant="outline"
                size="sm"
                disabled={reset.isPending}
                onClick={() => reset.mutate(unit.code)}
              >
                {t("unit.reset_grams")}
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}

      {settable.length > 0 ? (
        <div className="flex flex-wrap gap-2" data-testid="settable-units">
          {settable.map((c) => (
            <Button
              key={c}
              variant="outline"
              size="sm"
              data-testid={`set-${c}`}
              onClick={() => {
                setEditing(c);
                setGramsText("");
              }}
            >
              {t("unit.set_grams", {
                unit: unitLabel((k, v) => t(k as never, v as never), c, 1),
              })}
            </Button>
          ))}
        </div>
      ) : null}

      {editing !== null ? (
        <form
          noValidate
          onSubmit={saveGrams}
          className="space-y-2"
          data-testid="grams-form"
        >
          <label htmlFor={gramsId} className={labelClass}>
            {units.some((u) => u.code === editing)
              ? t("unit.edit_grams")
              : t("unit.set_grams", {
                  unit: unitLabel(
                    (k, v) => t(k as never, v as never),
                    editing,
                    1,
                  ),
                })}
          </label>
          <input
            id={gramsId}
            inputMode="decimal"
            value={gramsText}
            onChange={(e) => setGramsText(e.target.value)}
            data-allow-digits
            className={inputClass}
          />
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={put.isPending}>
              {t("meals.log.save")}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setEditing(null)}>
              {t("common.cancel")}
            </Button>
          </div>
        </form>
      ) : null}
      {portionError ? (
        <p role="alert" className="text-md text-text-primary">
          {errorText(portionError)}
        </p>
      ) : null}

      {preview && rows.length > 0 ? (
        <section
          data-testid="portion-preview"
          className="space-y-1 rounded-md bg-surface-muted p-3"
        >
          <dl className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 text-sm">
            {rows.map(([key, label]) => (
              <div key={key} className="contents">
                <dt className="text-text-secondary">{t(label)}</dt>
                <dd
                  data-testid={`preview-${key}`}
                  className="text-text-primary"
                >
                  {preview[key] === null || preview[key] === undefined
                    ? t("foods.not_known")
                    : preview[key]}
                </dd>
              </div>
            ))}
          </dl>
          <p className={hintClass}>{t("foods.preview_note")}</p>
        </section>
      ) : null}

      {dish && dish.ingredients.length > 0 ? (
        <section data-testid="dish-ingredients" className="space-y-1">
          <h4 className="text-sm font-semibold text-text-secondary">
            {t("foods.dish_ingredients")}
          </h4>
          <ul className="text-sm text-text-primary">
            {dish.ingredients.map((i) => (
              <li key={`${i.name}-${i.grams}`}>
                {i.name}
                {i.grams != null ? (
                  <span data-allow-digits>{` · ${i.grams} g`}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {food.review_pending ? (
        <p data-testid="review-pending" className={hintClass}>
          {t("foods.review_pending")}
        </p>
      ) : null}
      <SourceCredit keys={food.attributions} />

      {logError ? (
        <p role="alert" className="text-md text-text-primary">
          {errorText(logError)}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button onClick={save} disabled={!valid || log.isPending}>
          {t("foods.portion.save")}
        </Button>
        <Button variant="outline" onClick={onCancel}>
          {t("common.cancel")}
        </Button>
      </div>
    </div>
  );
}
