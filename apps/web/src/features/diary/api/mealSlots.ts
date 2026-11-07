import type { components } from "@smartnutri/api-client";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type MealSlotsOut = components["schemas"]["MealSlotsOut"];
export type MealSlotOut = components["schemas"]["MealSlotOut"];

export const mealSlotsKey = (includeArchived: boolean) =>
  ["meals", "slots", includeArchived] as const;

/** GET /v1/meal-slots: the slots and the one the server suggests right now. */
export function listMealSlots(includeArchived = false): Promise<MealSlotsOut> {
  const api = getApi();
  return call(
    api.GET("/v1/meal-slots", {
      params: { query: { include_archived: includeArchived } },
    }),
  );
}
