"use client";

import { useTranslations } from "next-intl";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { StarIcon } from "@/components/ui/icons";
import { LoadingState } from "@/components/ui/Skeleton";
import type { FoodHit } from "@/features/foods/api/foods";
import { PortionPicker } from "@/features/foods/components/PortionPicker";
import { SourceCredit } from "@/features/foods/components/SourceCredit";
import type { MealIn } from "@/features/meals/api/meals";
import { useLogMeal } from "@/features/meals/hooks/useMeals";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import type { FavouriteOut } from "../api/favourites";
import {
  useDeleteFavourite,
  useFavourites,
  useLogFavourite,
} from "../hooks/useFavourites";
import { mealItemAmount } from "../lib/mealItemLine";
import { FavouriteStar } from "./FavouriteStar";

const hitOf = (
  f: FavouriteOut,
): Pick<FoodHit, "kind" | "id" | "name" | "is_dish"> | null => {
  const base = { name: f.name, is_dish: false };
  if (f.food_id) return { ...base, kind: "food", id: f.food_id };
  if (f.custom_food_id)
    return { ...base, kind: "custom_food", id: f.custom_food_id };
  if (f.recipe_id) return { ...base, kind: "recipe", id: f.recipe_id };
  if (f.product_id) return { ...base, kind: "product", id: f.product_id };
  if (f.barcode) return { ...base, kind: "off", id: f.barcode };
  return null;
};

/**
 * The Favourites tab of the add-food panel. A food favourite logs its default
 * portion in one tap (a favourite with no default opens the portion picker);
 * "Choose portion" opens the picker either way. A meal favourite logs again
 * from its saved entries (one client_id per action, reused on retry); the
 * message is a count only. No numbers are shown on any row, so a hidden number
 * can never leak here. Names are user text: shown as typed, never sent on.
 */
export function FavouritesSegment({
  slotId,
  localDate,
  onLogged,
}: {
  slotId: string | null;
  localDate?: string;
  /** After a log; `count` is how many entries a meal favourite created. */
  onLogged: (count?: number) => void;
}) {
  const t = useTranslations();
  const list = useFavourites();
  const log = useLogMeal();
  const again = useLogFavourite();
  const remove = useDeleteFavourite();
  const [picking, setPicking] = useState<FavouriteOut | null>(null);
  const foodClient = useRef<string | null>(null);
  const mealClient = useRef<{ id: string; clientId: string } | null>(null);

  if (picking) {
    const hit = hitOf(picking);
    if (hit)
      return (
        <PortionPicker
          hit={hit}
          slotId={slotId}
          localDate={localDate}
          onLogged={() => onLogged()}
          onCancel={() => setPicking(null)}
          method="favourite"
        />
      );
  }

  function logFood(f: FavouriteOut) {
    const hit = hitOf(f);
    if (!hit) return;
    if (f.default_quantity == null || !f.default_unit) {
      setPicking(f);
      return;
    }
    foodClient.current ??= crypto.randomUUID();
    log.mutate(
      {
        ...(f.food_id
          ? { food_id: f.food_id }
          : f.custom_food_id
            ? { custom_food_id: f.custom_food_id }
            : f.recipe_id
              ? { recipe_id: f.recipe_id }
              : f.product_id
                ? { product_id: f.product_id }
                : { barcode: f.barcode }),
        quantity: f.default_quantity,
        unit: f.default_unit as NonNullable<MealIn["unit"]>,
        ...(slotId ? { meal_slot_id: slotId } : {}),
        ...(localDate ? { local_date: localDate } : {}),
        client_id: foodClient.current,
      },
      {
        onSuccess: () => {
          foodClient.current = null;
          track("diary_entry_added", { method: "favourite" });
          onLogged();
        },
      },
    );
  }

  function logMeal(f: FavouriteOut) {
    if (mealClient.current?.id !== f.id)
      mealClient.current = { id: f.id, clientId: crypto.randomUUID() };
    const clientId = mealClient.current.clientId;
    again.mutate(
      {
        id: f.id,
        body: {
          client_id: clientId,
          ...(slotId ? { meal_slot_id: slotId } : {}),
          ...(localDate ? { local_date: localDate } : {}),
        },
      },
      {
        onSuccess: (out) => {
          mealClient.current = null;
          track("diary_entry_added", { method: "favourite" });
          onLogged(out.created.length);
        },
      },
    );
  }

  if (list.isPending)
    return <LoadingState label={t("common.loading")} lines={2} />;
  if (list.isError)
    return (
      <ErrorState
        message={t(errorKey(t, list.error))}
        onRetry={() => void list.refetch()}
        retrying={list.isFetching}
      />
    );
  const items = list.data?.items ?? [];
  if (items.length === 0)
    return (
      <p data-testid="favourites-empty" className="text-md text-text-secondary">
        {t("favourites.empty")}
      </p>
    );

  const error = (log.error ?? again.error ?? remove.error) as ApiError | null;
  const busy = log.isPending || again.isPending;
  return (
    <div className="space-y-2">
      <ul className="divide-y divide-border-default" data-testid="favourites">
        {items.map((f) => (
          <li
            key={f.id}
            data-testid="favourite-item"
            data-kind={f.kind}
            className="flex min-h-11 items-center justify-between gap-2 py-2"
          >
            {f.kind === "meal" ? (
              <>
                <span className="min-w-0 text-md font-medium break-words text-text-primary">
                  {f.name}
                  <span
                    data-testid="favourite-meal-items"
                    data-allow-digits
                    className="block text-sm font-normal text-text-secondary"
                  >
                    {t("favourites.meal_items", { count: f.item_count })}
                  </span>
                  {(f.items ?? []).map((it, i) => (
                    <span
                      // biome-ignore lint/suspicious/noArrayIndexKey: a saved snapshot, never reordered
                      key={i}
                      data-testid="favourite-meal-item"
                      data-allow-digits
                      className="block text-sm font-normal text-text-secondary"
                    >
                      {[
                        it.name,
                        mealItemAmount((k, v) => t(k as never, v as never), it),
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                  ))}
                  <SourceCredit keys={f.attributions ?? []} />
                </span>
                <span className="flex shrink-0 items-center gap-1">
                  <Button
                    size="sm"
                    variant="secondary"
                    disabled={busy}
                    onClick={() => logMeal(f)}
                  >
                    {t("favourites.log_again")}
                  </Button>
                  <button
                    type="button"
                    data-testid="favourite-star"
                    aria-pressed
                    aria-label={t("favourites.remove")}
                    title={t("favourites.remove")}
                    disabled={remove.isPending}
                    onClick={() => remove.mutate(f.id)}
                    className="inline-flex size-11 cursor-pointer items-center justify-center rounded-full text-brand-primary hover:bg-surface-muted"
                  >
                    <StarIcon filled />
                  </button>
                </span>
              </>
            ) : (
              <>
                <button
                  type="button"
                  data-testid="favourite-food"
                  disabled={busy}
                  onClick={() => logFood(f)}
                  className="min-w-0 flex-1 cursor-pointer text-left text-md font-medium break-words text-text-primary hover:bg-surface-muted"
                >
                  {f.name}
                  <SourceCredit keys={f.attributions ?? []} />
                </button>
                <span className="flex shrink-0 items-center gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={busy || hitOf(f) === null}
                    onClick={() => setPicking(f)}
                  >
                    {t("foods.portion.title")}
                  </Button>
                  <FavouriteStar
                    foodRef={{
                      food_id: f.food_id,
                      product_id: f.product_id,
                      barcode: f.barcode,
                      custom_food_id: f.custom_food_id,
                      recipe_id: f.recipe_id,
                    }}
                    favouriteId={f.id}
                  />
                </span>
              </>
            )}
          </li>
        ))}
      </ul>
      {error ? (
        <p role="alert" className="text-md text-text-primary">
          {error.code === "network"
            ? t("meals.online_only")
            : t(errorKey(t, error))}
        </p>
      ) : null}
    </div>
  );
}
