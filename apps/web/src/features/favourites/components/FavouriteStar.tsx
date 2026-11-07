"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { StarIcon } from "@/components/ui/icons";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { ApiError } from "@/lib/api/errors";
import type { FavouriteIn } from "../api/favourites";
import { useAddFavourite, useDeleteFavourite } from "../hooks/useFavourites";

/**
 * Star or unstar a food. `favouriteId` is the member's favourite for it (null:
 * not starred). Starring saves `portion` (the chosen quantity and unit) as the
 * default when given. The food name never leaves this tab. A refused add
 * (limit, retired dish) shows its message.
 */
export function FavouriteStar({
  foodRef,
  favouriteId,
  portion,
}: {
  foodRef: Pick<
    FavouriteIn,
    "food_id" | "product_id" | "barcode" | "custom_food_id" | "recipe_id"
  >;
  favouriteId: string | null | undefined;
  portion?: {
    quantity: number;
    unit: NonNullable<FavouriteIn["default_unit"]>;
  } | null;
}) {
  const t = useTranslations();
  const add = useAddFavourite();
  const remove = useDeleteFavourite();
  const [override, setOverride] = useState<string | null | undefined>(
    undefined,
  );
  const id = override !== undefined ? override : (favouriteId ?? null);
  const starred = id !== null;
  const error = (add.error ?? remove.error) as ApiError | null;
  const busy = add.isPending || remove.isPending;

  function toggle() {
    if (id) {
      remove.mutate(id, { onSuccess: () => setOverride(null) });
    } else {
      add.mutate(
        {
          ...foodRef,
          ...(portion
            ? { default_quantity: portion.quantity, default_unit: portion.unit }
            : {}),
        },
        { onSuccess: (f) => setOverride(f.id) },
      );
    }
  }

  return (
    <span className="inline-flex flex-col items-end">
      <button
        type="button"
        data-testid="favourite-star"
        aria-pressed={starred}
        aria-label={starred ? t("favourites.remove") : t("favourites.add")}
        title={starred ? t("favourites.remove") : t("favourites.add")}
        disabled={busy}
        onClick={toggle}
        className="inline-flex size-11 cursor-pointer items-center justify-center rounded-full text-brand-primary hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary"
      >
        <StarIcon filled={starred} />
      </button>
      {error ? (
        <span
          role="alert"
          data-testid="favourite-error"
          className="text-sm text-text-primary"
        >
          {error.code === "network"
            ? t("meals.online_only")
            : t(errorKey(t, error))}
        </span>
      ) : null}
    </span>
  );
}
