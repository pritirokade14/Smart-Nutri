import type { components } from "@smartnutri/api-client";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type DiaryDayOut = components["schemas"]["DiaryDayOut"];
export type DiaryWeekOut = components["schemas"]["DiaryWeekOut"];
export type DayTile = components["schemas"]["DayTile"];
export type SlotDayOut = components["schemas"]["SlotDayOut"];
export type Macro4 = components["schemas"]["Macro4"];
export type MealOut = components["schemas"]["MealOut"];
export type MealPatch = components["schemas"]["MealPatch"];
export type QuickIn = components["schemas"]["QuickIn"];
export type CopyIn = components["schemas"]["CopyIn"];
export type CopyOut = components["schemas"]["CopyOut"];
export type RecentItem = components["schemas"]["RecentItem"];
export type RecentsOut = components["schemas"]["RecentsOut"];

/**
 * Diary query keys live under ["meals"], so the existing sign-out purge
 * (clearMealsCache) and every meal write refresh them. They hold personal
 * and health data and are never sent to analytics.
 */
export const diaryDayKey = (date: string | undefined) =>
  ["meals", "diary", "day", date ?? "today"] as const;
export const diaryWeekKey = (end: string | undefined) =>
  ["meals", "diary", "week", end ?? "today"] as const;
export const recentsKey = (slotId: string | undefined) =>
  ["meals", "diary", "recents", slotId ?? "any"] as const;

/** GET /v1/diary/day: everything on the day is computed by the API. */
export function getDiaryDay(date?: string): Promise<DiaryDayOut> {
  const api = getApi();
  return call(
    api.GET("/v1/diary/day", { params: { query: date ? { date } : {} } }),
  );
}

/** GET /v1/diary/week: seven day tiles, oldest first. */
export function getDiaryWeek(end?: string): Promise<DiaryWeekOut> {
  const api = getApi();
  return call(
    api.GET("/v1/diary/week", { params: { query: end ? { end } : {} } }),
  );
}

/** PATCH /v1/meals/{id}: only the fields set are sent (null = unchanged). */
export function updateMeal(mealId: string, patch: MealPatch): Promise<MealOut> {
  const api = getApi();
  return call(
    api.PATCH("/v1/meals/{meal_id}", {
      params: { path: { meal_id: mealId } },
      body: patch,
    }),
  );
}

/** PUT /v1/diary/days/{date}/status: mark a day as partly logged (or not). */
export function putDayStatus(
  date: string,
  partialLogged: boolean,
): Promise<components["schemas"]["DiaryDayStatusOut"]> {
  const api = getApi();
  return call(
    api.PUT("/v1/diary/days/{day}/status", {
      params: { path: { day: date } },
      body: { partial_logged: partialLogged },
    }),
  );
}

/** GET /v1/diary/recents: what was eaten lately, the given slot first. */
export function getRecents(slotId?: string): Promise<RecentsOut> {
  const api = getApi();
  return call(
    api.GET("/v1/diary/recents", {
      params: { query: slotId ? { slot_id: slotId } : {} },
    }),
  );
}

/** POST /v1/meals/copy: the same client_id on a retry creates nothing twice. */
export function copyMeals(body: CopyIn): Promise<CopyOut> {
  const api = getApi();
  return call(api.POST("/v1/meals/copy", { body }));
}
