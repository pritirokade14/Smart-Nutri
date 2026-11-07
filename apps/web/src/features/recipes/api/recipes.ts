import type { components } from "@smartnutri/api-client";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type RecipeIn = components["schemas"]["RecipeIn"];
export type RecipeOut = components["schemas"]["RecipeOut"];
export type RecipesOut = components["schemas"]["RecipesOut"];
export type RecipeSummaryOut = components["schemas"]["RecipeSummaryOut"];
export type RecipeIngredientIn = components["schemas"]["RecipeIngredientIn"];
export type RecipeIngredientOut = components["schemas"]["RecipeIngredientOut"];

export const recipesKey = ["meals", "recipes"] as const;
export const recipeKey = (id: string) => ["meals", "recipes", id] as const;

export function listRecipes(
  cursor?: string | null,
  limit = 50,
): Promise<RecipesOut> {
  const api = getApi();
  return call(
    api.GET("/v1/recipes", {
      params: { query: { limit, ...(cursor ? { cursor } : {}) } },
    }),
  );
}

export function getRecipe(id: string): Promise<RecipeOut> {
  const api = getApi();
  return call(
    api.GET("/v1/recipes/{recipe_id}", { params: { path: { recipe_id: id } } }),
  );
}

export function createRecipe(body: RecipeIn): Promise<RecipeOut> {
  const api = getApi();
  return call(api.POST("/v1/recipes", { body }));
}

export function updateRecipe(id: string, body: RecipeIn): Promise<RecipeOut> {
  const api = getApi();
  return call(
    api.PUT("/v1/recipes/{recipe_id}", {
      params: { path: { recipe_id: id } },
      body,
    }),
  );
}

export async function deleteRecipe(id: string): Promise<void> {
  const api = getApi();
  await call(
    api.DELETE("/v1/recipes/{recipe_id}", {
      params: { path: { recipe_id: id } },
    }),
  );
}
