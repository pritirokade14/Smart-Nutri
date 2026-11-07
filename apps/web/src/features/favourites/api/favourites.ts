import type { components } from "@smartnutri/api-client";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type FavouriteOut = components["schemas"]["FavouriteOut"];
export type FavouritesOut = components["schemas"]["FavouritesOut"];
export type FavouriteIn = components["schemas"]["FavouriteIn"];
export type FavouriteMealIn = components["schemas"]["FavouriteMealIn"];
export type FavouriteLogIn = components["schemas"]["FavouriteLogIn"];
export type FavouriteLogOut = components["schemas"]["FavouriteLogOut"];

/**
 * Favourites hold the user's own meal names (user text): under ["meals"], so
 * the sign-out purge drops them. Never sent to analytics or logs.
 */
export const favouritesKey = ["meals", "favourites"] as const;

export function listFavourites(): Promise<FavouritesOut> {
  return call(getApi().GET("/v1/favourites"));
}

export function addFavourite(body: FavouriteIn): Promise<FavouriteOut> {
  return call(getApi().POST("/v1/favourites", { body }));
}

export function addFavouriteMeal(body: FavouriteMealIn): Promise<FavouriteOut> {
  return call(getApi().POST("/v1/favourites/meals", { body }));
}

export async function deleteFavourite(id: string): Promise<void> {
  await call(
    getApi().DELETE("/v1/favourites/{favourite_id}", {
      params: { path: { favourite_id: id } },
    }),
  );
}

export function logFavourite(
  id: string,
  body: FavouriteLogIn,
): Promise<FavouriteLogOut> {
  return call(
    getApi().POST("/v1/favourites/{favourite_id}/log", {
      params: { path: { favourite_id: id } },
      body,
    }),
  );
}

/** The food reference a favourite (or a log) uses, from a search hit kind. */
export function foodRef(
  kind: "food" | "product" | "off" | "custom_food" | "recipe",
  id: string,
): Pick<
  FavouriteIn,
  "food_id" | "product_id" | "barcode" | "custom_food_id" | "recipe_id"
> {
  return kind === "food"
    ? { food_id: id }
    : kind === "product"
      ? { product_id: id }
      : kind === "custom_food"
        ? { custom_food_id: id }
        : kind === "recipe"
          ? { recipe_id: id }
          : { barcode: id };
}

/** Whether a food favourite points at this reference. */
export function sameRef(
  f: FavouriteOut,
  ref: ReturnType<typeof foodRef>,
): boolean {
  return (
    f.kind === "food" &&
    (ref.food_id ? f.food_id === ref.food_id : true) &&
    (ref.product_id ? f.product_id === ref.product_id : true) &&
    (ref.barcode ? f.barcode === ref.barcode : true) &&
    (ref.custom_food_id ? f.custom_food_id === ref.custom_food_id : true) &&
    (ref.recipe_id ? f.recipe_id === ref.recipe_id : true)
  );
}
