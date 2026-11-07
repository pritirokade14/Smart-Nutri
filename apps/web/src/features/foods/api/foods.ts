import type { components } from "@smartnutri/api-client";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type FoodHit = components["schemas"]["FoodHit"];
export type FoodSearchOut = components["schemas"]["FoodSearchOut"];
export type FoodDetailOut = components["schemas"]["FoodDetailOut"];
export type FoodUnitOut = components["schemas"]["FoodUnitOut"];
export type FoodKind = components["schemas"]["FoodKindPath"];
export type UnitCode = NonNullable<components["schemas"]["MealIn"]["unit"]>;

/**
 * Food details hold the member's own measures and the hidden-numbers
 * redaction, so they live under ["meals"]: the sign-out purge drops them.
 */
export const foodKey = (kind: FoodKind, id: string) =>
  ["meals", "foods", "detail", kind, id] as const;
export const foodSearchKey = (q: string) =>
  ["meals", "foods", "search", q] as const;

/** GET /v1/foods/search: Indian foods and dishes first, then packaged. */
export function searchFoods(q: string): Promise<FoodSearchOut> {
  const api = getApi();
  return call(api.GET("/v1/foods/search", { params: { query: { q } } }));
}

/** GET /v1/foods/{kind}/{id}: only the units that resolve, as the API says. */
export function getFood(kind: FoodKind, id: string): Promise<FoodDetailOut> {
  const api = getApi();
  return call(
    api.GET("/v1/foods/{kind}/{id}", { params: { path: { kind, id } } }),
  );
}

/** PUT /v1/foods/{kind}/{id}/portions/{unit}: the account's own grams. */
export function putPortion(
  kind: FoodKind,
  id: string,
  unit: string,
  gramsPerUnit: number,
): Promise<FoodDetailOut> {
  const api = getApi();
  return call(
    api.PUT("/v1/foods/{kind}/{id}/portions/{unit}", {
      params: { path: { kind, id, unit } },
      body: { grams_per_unit: gramsPerUnit },
    }),
  );
}

/** DELETE /v1/foods/{kind}/{id}/portions/{unit}: back to the standard value. */
export async function deletePortion(
  kind: FoodKind,
  id: string,
  unit: string,
): Promise<void> {
  const api = getApi();
  await call(
    api.DELETE("/v1/foods/{kind}/{id}/portions/{unit}", {
      params: { path: { kind, id, unit } },
    }),
  );
}
