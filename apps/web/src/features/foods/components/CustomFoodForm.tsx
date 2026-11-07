"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { chipClass } from "@/components/ui/Chip";
import { ConfirmDialog } from "@/components/ui/Dialog";
import { ErrorState } from "@/components/ui/ErrorState";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { LoadingState } from "@/components/ui/Skeleton";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { ApiError } from "@/lib/api/errors";
import type {
  CustomFoodIn,
  CustomFoodOut,
  CustomNutrientsIn,
} from "../api/customFoods";
import {
  useCustomFoodById,
  useDeleteCustomFood,
  useSaveCustomFood,
} from "../hooks/useCustomFoods";
import { unitLabel } from "../lib/unitLabel";

type NutrientKey = keyof CustomNutrientsIn;

// Existing catalogue keys, in display order. Every one is optional: a blank is
// unknown and is sent as absent, never 0.
const FIELDS: readonly (readonly [NutrientKey, string])[] = [
  ["energy_kcal", "confirm.field.energy_kcal"],
  ["protein_g", "confirm.field.protein_g"],
  ["carbs_g", "confirm.field.carbs_g"],
  ["fat_g", "confirm.field.fat_g"],
  ["sugars_g", "custom_food.field.sugars"],
  ["sat_fat_g", "custom_food.field.sat_fat"],
  ["fibre_g", "confirm.field.fiber_g"],
  ["salt_g", "custom_food.field.salt"],
  ["sodium_mg", "custom_food.field.sodium"],
];

// Household measures the member can give grams for (count and volume units).
const PORTION_UNITS = [
  "piece",
  "piece_small",
  "piece_medium",
  "piece_large",
  "roti",
  "slice",
  "katori",
  "katori_small",
  "katori_medium",
  "katori_large",
  "cup",
  "glass",
  "tbsp",
  "tsp",
] as const;

/** A non-negative number, null for a blank, undefined for an invalid text. */
function parse(raw: string): number | null | undefined {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) && n >= 0 ? n : undefined;
}

type Portion = { unit: string; grams: string };

const text = (v: number | null | undefined) => (v == null ? "" : String(v));

export function CustomFoodForm({ id }: { id?: string }) {
  return id ? <Edit id={id} /> : <Loaded />;
}

function Edit({ id }: { id: string }) {
  const t = useTranslations();
  const found = useCustomFoodById(id);
  if (found.isPending) return <LoadingState label={t("common.loading")} />;
  if (found.isError)
    return (
      <ErrorState
        message={t(errorKey(t, found.error))}
        onRetry={() => void found.refetch()}
      />
    );
  if (!found.food && found.hasNextPage) {
    // Keep paging until the food turns up (the API has no single read).
    if (!found.isFetchingNextPage) void found.fetchNextPage();
    return <LoadingState label={t("common.loading")} />;
  }
  if (!found.food)
    return <ErrorState message={t("error.custom_food_not_found")} />;
  return <Loaded food={found.food} />;
}

function Loaded({ food }: { food?: CustomFoodOut }) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const ids = {
    name: useId(),
    brand: useId(),
    serving: useId(),
    density: useId(),
    barcode: useId(),
    unit: useId(),
    grams: useId(),
  };
  const save = useSaveCustomFood(food?.id);
  const del = useDeleteCustomFood();
  const clientId = useRef<string | null>(null);
  const [name, setName] = useState(food?.name ?? "");
  const [brand, setBrand] = useState(food?.brand ?? "");
  const [basis, setBasis] = useState<"g" | "ml">(
    (food?.basis as "g" | "ml") ?? "g",
  );
  const [valuesPer, setValuesPer] = useState<"100" | "serving">(
    (food?.entered.values_per as "100" | "serving") ?? "100",
  );
  const [serving, setServing] = useState(text(food?.entered.serving_g));
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(
      FIELDS.map(([k]) => [k, text(food?.entered.nutrients[k])]),
    ),
  );
  const [density, setDensity] = useState(text(food?.density_g_per_ml));
  const [barcode, setBarcode] = useState(food?.barcode ?? "");
  const [portions, setPortions] = useState<Portion[]>(
    (food?.portions ?? []).map((p) => ({
      unit: p.unit,
      grams: String(p.grams_per_unit),
    })),
  );
  const [pickUnit, setPickUnit] = useState<string>(PORTION_UNITS[0]);
  const [pickGrams, setPickGrams] = useState("");
  const [problem, setProblem] = useState<"name" | "number" | null>(null);
  const [confirming, setConfirming] = useState(false);

  const tt = (k: string, v?: Record<string, string | number>) =>
    t(k as never, v as never);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (name.trim() === "") return setProblem("name");
    const nutrients: CustomNutrientsIn = {};
    for (const [k] of FIELDS) {
      const v = parse(values[k]);
      if (v === undefined) return setProblem("number");
      if (v !== null) nutrients[k] = v; // blank: absent, never 0
    }
    const servingG = parse(serving);
    const densityG = parse(density);
    if (
      servingG === undefined ||
      densityG === undefined ||
      (valuesPer === "serving" && (servingG === null || servingG <= 0))
    )
      return setProblem("number");
    const rows: { unit: string; grams_per_unit: number }[] = [];
    for (const p of portions) {
      const g = parse(p.grams);
      if (g === undefined || g === null || g <= 0) return setProblem("number");
      rows.push({ unit: p.unit, grams_per_unit: g });
    }
    setProblem(null);
    clientId.current ??= crypto.randomUUID();
    const body: CustomFoodIn = {
      name: name.trim(),
      ...(brand.trim() ? { brand: brand.trim() } : {}),
      basis,
      values_per: valuesPer,
      ...(valuesPer === "serving" && servingG ? { serving_g: servingG } : {}),
      nutrients,
      ...(basis === "ml" && densityG ? { density_g_per_ml: densityG } : {}),
      ...(barcode.trim() ? { barcode: barcode.trim() } : {}),
      ...(rows.length ? { portions: rows as CustomFoodIn["portions"] } : {}),
      ...(food ? {} : { client_id: clientId.current }),
    };
    save.mutate(body, {
      onSuccess: () => router.push(`/${locale}/diary/my-foods`),
    });
  }

  function addPortion() {
    const g = parse(pickGrams);
    if (g === null || g === undefined || g <= 0) return;
    setPortions((rows) => [
      ...rows.filter((r) => r.unit !== pickUnit),
      { unit: pickUnit, grams: String(g) },
    ]);
    setPickGrams("");
  }

  const error = (save.error ?? del.error) as ApiError | null;
  const badFields = Array.isArray(error?.details?.fields)
    ? (error?.details?.fields as string[])
    : [];
  const invalid = (k: NutrientKey) =>
    badFields.some((f) => f.endsWith(`.${k}`)) || undefined;

  return (
    <form
      noValidate
      onSubmit={submit}
      data-testid="custom-food-form"
      className="space-y-4"
    >
      <div className="space-y-1">
        <label htmlFor={ids.name} className={labelClass}>
          {t("custom_food.name")}
        </label>
        <input
          id={ids.name}
          value={name}
          maxLength={80}
          aria-invalid={problem === "name" || undefined}
          onChange={(e) => setName(e.target.value)}
          className={inputClass}
        />
      </div>
      <div className="space-y-1">
        <label htmlFor={ids.brand} className={labelClass}>
          {t("custom_food.brand")}
        </label>
        <input
          id={ids.brand}
          value={brand}
          maxLength={80}
          onChange={(e) => setBrand(e.target.value)}
          className={inputClass}
        />
      </div>

      <fieldset className="m-0 flex flex-wrap gap-4 border-0 p-0">
        {(["g", "ml"] as const).map((b) => (
          <label key={b} className="flex items-center gap-2 text-md">
            <input
              type="radio"
              name="basis"
              checked={basis === b}
              onChange={() => setBasis(b)}
            />
            {t(b === "g" ? "custom_food.basis_g" : "custom_food.basis_ml")}
          </label>
        ))}
      </fieldset>
      <fieldset className="m-0 flex flex-wrap gap-4 border-0 p-0">
        {(["100", "serving"] as const).map((v) => (
          <label key={v} className="flex items-center gap-2 text-md">
            <input
              type="radio"
              name="values_per"
              checked={valuesPer === v}
              onChange={() => setValuesPer(v)}
            />
            {t(
              v === "serving"
                ? "foods.values_per.serving"
                : basis === "ml"
                  ? "foods.values_per.100ml"
                  : "foods.values_per.100g",
            )}
          </label>
        ))}
      </fieldset>
      {valuesPer === "serving" ? (
        <div className="space-y-1">
          <label htmlFor={ids.serving} className={labelClass}>
            {t("custom_food.serving_size")}
          </label>
          <input
            id={ids.serving}
            inputMode="decimal"
            value={serving}
            onChange={(e) => setServing(e.target.value)}
            data-allow-digits
            className={inputClass}
          />
        </div>
      ) : null}

      {FIELDS.map(([k, label]) => (
        <div key={k} className="space-y-1">
          <label htmlFor={`${ids.name}-${k}`} className={labelClass}>
            {t(label)}
          </label>
          <input
            id={`${ids.name}-${k}`}
            inputMode="decimal"
            value={values[k]}
            aria-invalid={invalid(k)}
            onChange={(e) => setValues((v) => ({ ...v, [k]: e.target.value }))}
            data-allow-digits
            className={inputClass}
          />
        </div>
      ))}
      <p className={hintClass}>{t("foods.blank_is_unknown")}</p>

      {basis === "ml" ? (
        <div className="space-y-1">
          <label htmlFor={ids.density} className={labelClass}>
            {t("custom_food.density")}
          </label>
          <input
            id={ids.density}
            inputMode="decimal"
            value={density}
            onChange={(e) => setDensity(e.target.value)}
            data-allow-digits
            className={inputClass}
          />
          <p className={hintClass}>{t("custom_food.density_hint")}</p>
        </div>
      ) : null}

      <div className="space-y-1">
        <label htmlFor={ids.barcode} className={labelClass}>
          {t("custom_food.barcode")}
        </label>
        <input
          id={ids.barcode}
          inputMode="numeric"
          value={barcode}
          onChange={(e) => setBarcode(e.target.value)}
          data-allow-digits
          className={inputClass}
        />
      </div>

      <fieldset
        className="m-0 space-y-2 border-0 p-0"
        data-testid="custom-portions"
      >
        <legend className={labelClass}>{t("custom_food.portions")}</legend>
        <ul className="flex flex-wrap gap-2">
          {portions.map((p) => (
            <li key={p.unit} className={chipClass} data-allow-digits>
              {tt("diary.portion_line", {
                quantity: "1",
                unit: unitLabel(tt, p.unit, 1),
                grams: p.grams,
              })}
              <button
                type="button"
                className="cursor-pointer underline"
                onClick={() =>
                  setPortions((rows) => rows.filter((r) => r.unit !== p.unit))
                }
              >
                {t("diary.delete")}
              </button>
            </li>
          ))}
        </ul>
        <div className="flex flex-wrap items-end gap-2">
          <select
            aria-label={t("custom_food.portions")}
            value={pickUnit}
            onChange={(e) => setPickUnit(e.target.value)}
            className={inputClass.replace("block w-full", "w-auto")}
          >
            {PORTION_UNITS.map((u) => (
              <option key={u} value={u}>
                {unitLabel(tt, u, 1)}
              </option>
            ))}
          </select>
          <div className="space-y-1">
            <label htmlFor={ids.grams} className="sr-only">
              {tt("unit.set_grams", { unit: unitLabel(tt, pickUnit, 1) })}
            </label>
            <input
              id={ids.grams}
              inputMode="decimal"
              value={pickGrams}
              placeholder="g"
              onChange={(e) => setPickGrams(e.target.value)}
              data-allow-digits
              className={inputClass.replace("block w-full", "w-28")}
            />
          </div>
          <Button variant="outline" size="sm" onClick={addPortion}>
            {t("foods.portion.save")}
          </Button>
        </div>
      </fieldset>

      {problem ? (
        <p role="alert" className="text-md text-text-primary">
          {t("error.validation_error")}
        </p>
      ) : null}
      {error ? (
        <p role="alert" className="text-md text-text-primary">
          {error.code === "network"
            ? t("meals.online_only")
            : t(errorKey(t, error))}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={save.isPending}>
          {t("custom_food.save")}
        </Button>
        {food ? (
          <Button variant="outline" onClick={() => setConfirming(true)}>
            {t("custom_food.delete")}
          </Button>
        ) : null}
      </div>
      {confirming && food ? (
        <ConfirmDialog
          message={
            <>
              {t("custom_food.delete_confirm")}
              <span className="mt-1 block text-sm font-normal text-text-secondary">
                {t("custom_food.history_kept")}
              </span>
            </>
          }
          confirmLabel={t("custom_food.delete")}
          cancelLabel={t("common.cancel")}
          busy={del.isPending}
          onCancel={() => setConfirming(false)}
          onConfirm={() =>
            del.mutate(food.id, {
              onSuccess: () => router.push(`/${locale}/diary/my-foods`),
              onSettled: () => setConfirming(false),
            })
          }
        />
      ) : null}
    </form>
  );
}
