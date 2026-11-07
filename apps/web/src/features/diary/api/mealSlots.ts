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

export type MealSlotCreateIn = components["schemas"]["MealSlotCreateIn"];
export type MealSlotRenameIn = components["schemas"]["MealSlotRenameIn"];
export type MealSlotArchiveOut = { result: "archived" | "deleted" };

/** POST /v1/meal-slots: the label is the user's own text, sent as typed. */
export function createMealSlot(body: MealSlotCreateIn): Promise<MealSlotOut> {
  const api = getApi();
  return call(api.POST("/v1/meal-slots", { body }));
}

/** PATCH /v1/meal-slots/{id}: null fields are unchanged; the clear flags remove. */
export function renameMealSlot(
  slotId: string,
  body: Partial<MealSlotRenameIn>,
): Promise<MealSlotOut> {
  const api = getApi();
  return call(
    api.PATCH("/v1/meal-slots/{slot_id}", {
      params: { path: { slot_id: slotId } },
      body: body as MealSlotRenameIn,
    }),
  );
}

/** PUT /v1/meal-slots/order: every active id exactly once. */
export function reorderMealSlots(ids: string[]) {
  const api = getApi();
  return call(api.PUT("/v1/meal-slots/order", { body: { ids } }));
}

/** DELETE /v1/meal-slots/{id}: archived when it has entries, else deleted. */
export function archiveMealSlot(slotId: string): Promise<MealSlotArchiveOut> {
  const api = getApi();
  return call(
    api.DELETE("/v1/meal-slots/{slot_id}", {
      params: { path: { slot_id: slotId } },
    }),
  ) as Promise<MealSlotArchiveOut>;
}
