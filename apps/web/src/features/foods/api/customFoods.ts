import type { components } from "@smartnutri/api-client";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type CustomFoodIn = components["schemas"]["CustomFoodIn"];
export type CustomFoodOut = components["schemas"]["CustomFoodOut"];
export type CustomFoodsOut = components["schemas"]["CustomFoodsOut"];
export type CustomNutrientsIn = components["schemas"]["CustomNutrientsIn"];

/** The user's own foods are personal data: under ["meals"], purged on sign-out. */
export const customFoodsKey = ["meals", "custom-foods"] as const;

export function listCustomFoods(
  cursor?: string | null,
  limit = 50,
): Promise<CustomFoodsOut> {
  const api = getApi();
  return call(
    api.GET("/v1/custom-foods", {
      params: { query: { limit, ...(cursor ? { cursor } : {}) } },
    }),
  );
}

export function createCustomFood(body: CustomFoodIn): Promise<CustomFoodOut> {
  const api = getApi();
  return call(api.POST("/v1/custom-foods", { body }));
}

/** A FULL replace: a nutrient left out becomes unknown. */
export function updateCustomFood(
  id: string,
  body: CustomFoodIn,
): Promise<CustomFoodOut> {
  const api = getApi();
  return call(
    api.PUT("/v1/custom-foods/{food_id}", {
      params: { path: { food_id: id } },
      body,
    }),
  );
}

export async function deleteCustomFood(id: string): Promise<void> {
  const api = getApi();
  await call(
    api.DELETE("/v1/custom-foods/{food_id}", {
      params: { path: { food_id: id } },
    }),
  );
}
