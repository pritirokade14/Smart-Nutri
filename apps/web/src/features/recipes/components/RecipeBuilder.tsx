"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog, Dialog } from "@/components/ui/Dialog";
import { ErrorState } from "@/components/ui/ErrorState";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { LoadingState } from "@/components/ui/Skeleton";
import { FoodSearch } from "@/features/foods/components/FoodSearch";
import {
  type IngredientPick,
  PortionPicker,
} from "@/features/foods/components/PortionPicker";
import { SourceCredit } from "@/features/foods/components/SourceCredit";
import { unitLabel } from "@/features/foods/lib/unitLabel";
import { formatAmount } from "@/features/history/lib/summary";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { ApiError } from "@/lib/api/errors";
import type {
  RecipeIn,
  RecipeIngredientIn,
  RecipeIngredientOut,
  RecipeOut,
} from "../api/recipes";
import { useDeleteRecipe, useRecipe, useSaveRecipe } from "../hooks/useRecipes";
import { RecipeNutrients } from "./RecipeNutrients";

type Row = {
  uid: string;
  ref: Pick<
    RecipeIngredientIn,
    "food_id" | "custom_food_id" | "product_id" | "barcode"
  >;
  name: string;
  quantity: number;
  unit: string;
  available: boolean;
  attribution: string | null;
};

const refOf = (p: IngredientPick): Row["ref"] =>
  p.kind === "food"
    ? { food_id: p.id }
    : p.kind === "custom_food"
      ? { custom_food_id: p.id }
      : p.kind === "product"
        ? { product_id: p.id }
        : { barcode: p.id };

const fromOut = (i: RecipeIngredientOut): Row => ({
  uid: crypto.randomUUID(),
  ref: i.food_id
    ? { food_id: i.food_id }
    : i.custom_food_id
      ? { custom_food_id: i.custom_food_id }
      : i.product_id
        ? { product_id: i.product_id }
        : { barcode: i.barcode },
  name: i.name,
  quantity: i.quantity,
  unit: i.unit,
  available: i.available,
  attribution: i.attribution,
});

const num = (raw: string): number | null | undefined => {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) && n > 0 ? n : undefined;
};

export function RecipeBuilder({ id }: { id?: string }) {
  return id ? <Edit id={id} /> : <Builder />;
}

function Edit({ id }: { id: string }) {
  const t = useTranslations();
  const recipe = useRecipe(id);
  if (recipe.isPending) return <LoadingState label={t("common.loading")} />;
  if (recipe.isError)
    return (
      <ErrorState
        message={t(errorKey(t, recipe.error))}
        onRetry={() => void recipe.refetch()}
        retrying={recipe.isFetching}
      />
    );
  return <Builder saved={recipe.data} />;
}

/**
 * The recipe builder. Ingredients come through the same search and portion
 * picker as the diary (ingredient mode: nothing is logged). Before saving it
 * shows the ingredient list only. After saving, the nutrients are the API's
 * (RecipeNutrients). An ingredient that was deleted must be replaced first.
 */
function Builder({ saved }: { saved?: RecipeOut }) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const ids = { name: useId(), servings: useId(), weight: useId() };
  const [recipeId, setRecipeId] = useState(saved?.id);
  const save = useSaveRecipe(recipeId);
  const del = useDeleteRecipe();
  const clientId = useRef<string | null>(null);
  const [result, setResult] = useState<RecipeOut | undefined>(saved);
  const [name, setName] = useState(saved?.name ?? "");
  const [servings, setServings] = useState(
    saved?.servings != null ? String(saved.servings) : "",
  );
  const [weight, setWeight] = useState(
    saved?.cooked_weight_g != null ? String(saved.cooked_weight_g) : "",
  );
  const [rows, setRows] = useState<Row[]>(
    (saved?.ingredients ?? []).map(fromOut),
  );
  const [adding, setAdding] = useState(false);
  const [hit, setHit] = useState<
    Parameters<typeof PortionPicker>[0]["hit"] | null
  >(null);
  const [logging, setLogging] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [problem, setProblem] = useState(false);

  const tt = (k: string, v?: Record<string, string | number>) =>
    t(k as never, v as never);
  const blocked = rows.some((r) => !r.available);

  function submit() {
    const s = num(servings);
    const w = num(weight);
    if (
      name.trim() === "" ||
      rows.length === 0 ||
      s === undefined ||
      w === undefined ||
      blocked
    ) {
      setProblem(true);
      return;
    }
    setProblem(false);
    clientId.current ??= crypto.randomUUID();
    const body: RecipeIn = {
      name: name.trim(),
      ...(s !== null ? { servings: s } : {}),
      ...(w !== null ? { cooked_weight_g: w } : {}),
      ingredients: rows.map((r) => ({
        ...r.ref,
        quantity: r.quantity,
        unit: r.unit as RecipeIngredientIn["unit"],
      })),
      ...(recipeId ? {} : { client_id: clientId.current }),
    };
    save.mutate(body, {
      onSuccess: (out) => {
        setResult(out);
        setRecipeId(out.id);
        setRows(out.ingredients.map(fromOut));
      },
    });
  }

  function pick(p: IngredientPick) {
    setRows((r) => [
      ...r,
      {
        uid: crypto.randomUUID(),
        ref: refOf(p),
        name: p.name,
        quantity: p.quantity,
        unit: p.unit,
        available: true,
        attribution: null,
      },
    ]);
    setHit(null);
    setAdding(false);
  }

  const error = (save.error ?? del.error) as ApiError | null;
  const credits = [
    ...new Set([
      ...(result?.attributions ?? []),
      ...rows.flatMap((r) => (r.attribution ? [r.attribution] : [])),
    ]),
  ];

  return (
    <div className="space-y-4" data-testid="recipe-builder">
      <div className="space-y-1">
        <label htmlFor={ids.name} className={labelClass}>
          {t("recipes.name")}
        </label>
        <input
          id={ids.name}
          value={name}
          maxLength={80}
          aria-invalid={(problem && name.trim() === "") || undefined}
          onChange={(e) => setName(e.target.value)}
          className={inputClass}
        />
      </div>

      <section className="space-y-2" data-testid="recipe-ingredients">
        <h2 className="text-md font-semibold text-text-primary">
          {t("recipes.ingredients")}
        </h2>
        <ul className="divide-y divide-border-default">
          {rows.map((r, i) => (
            <li
              key={r.uid}
              data-testid="recipe-ingredient"
              className="flex flex-wrap items-center justify-between gap-2 py-2"
            >
              <span className="min-w-0 text-md break-words text-text-primary">
                {r.name}
                <span
                  className="block text-sm text-text-secondary"
                  data-allow-digits
                >
                  {formatAmount(r.quantity)} {unitLabel(tt, r.unit, r.quantity)}
                </span>
                {!r.available ? (
                  <span
                    role="alert"
                    data-testid="ingredient-unavailable"
                    className="block text-sm text-text-primary"
                  >
                    {t("recipes.ingredient_unavailable")}
                  </span>
                ) : null}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setRows((all) => all.filter((_, j) => j !== i))}
              >
                {t("diary.delete")}
              </Button>
            </li>
          ))}
        </ul>
        <Button variant="outline" onClick={() => setAdding(true)}>
          {t("recipes.add_ingredient")}
        </Button>
      </section>

      <div className="space-y-1">
        <label htmlFor={ids.servings} className={labelClass}>
          {t("recipes.servings")}
        </label>
        <input
          id={ids.servings}
          inputMode="decimal"
          value={servings}
          onChange={(e) => setServings(e.target.value)}
          data-allow-digits
          className={inputClass}
        />
      </div>
      <div className="space-y-1">
        <label htmlFor={ids.weight} className={labelClass}>
          {t("recipes.cooked_weight")}
        </label>
        <input
          id={ids.weight}
          inputMode="decimal"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
          data-allow-digits
          className={inputClass}
        />
        <p className={hintClass}>{t("recipes.cooked_weight_tip")}</p>
      </div>

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
        <Button onClick={submit} disabled={save.isPending || blocked}>
          {t("members.form.save")}
        </Button>
        {recipeId ? (
          <Button variant="outline" onClick={() => setConfirming(true)}>
            {t("diary.delete")}
          </Button>
        ) : null}
      </div>

      {result && !save.isPending ? (
        <section className="space-y-3" data-testid="recipe-saved">
          <p role="status" className="text-md text-text-primary">
            {t("recipes.saved")}
          </p>
          <RecipeNutrients recipe={result} />
          <SourceCredit keys={credits} />
          <Button onClick={() => setLogging(true)}>
            {t("recipes.log_serving")}
          </Button>
        </section>
      ) : null}

      {adding ? (
        <Dialog
          title={t("recipes.add_ingredient")}
          testId="ingredient-dialog"
          onClose={() => {
            setAdding(false);
            setHit(null);
          }}
          actions={
            <Button
              variant="outline"
              onClick={() => {
                setAdding(false);
                setHit(null);
              }}
            >
              {t("common.close")}
            </Button>
          }
        >
          {hit ? (
            <PortionPicker
              hit={hit}
              slotId={null}
              ingredient={pick}
              onLogged={() => undefined}
              onCancel={() => setHit(null)}
            />
          ) : (
            <FoodSearch onPick={setHit} />
          )}
        </Dialog>
      ) : null}

      {logging && recipeId ? (
        <Dialog
          title={t("recipes.log_serving")}
          testId="log-recipe-dialog"
          onClose={() => setLogging(false)}
          actions={
            <Button variant="outline" onClick={() => setLogging(false)}>
              {t("common.close")}
            </Button>
          }
        >
          <PortionPicker
            hit={{
              kind: "recipe",
              id: recipeId,
              name: name.trim(),
              is_dish: false,
            }}
            slotId={null}
            onLogged={() => router.push(`/${locale}/diary`)}
            onCancel={() => setLogging(false)}
          />
        </Dialog>
      ) : null}

      {confirming && recipeId ? (
        <ConfirmDialog
          message={t("recipes.delete_confirm")}
          confirmLabel={t("diary.delete")}
          cancelLabel={t("common.cancel")}
          busy={del.isPending}
          onCancel={() => setConfirming(false)}
          onConfirm={() =>
            del.mutate(recipeId, {
              onSuccess: () => router.push(`/${locale}/diary/my-foods`),
              onSettled: () => setConfirming(false),
            })
          }
        />
      ) : null}
    </div>
  );
}
