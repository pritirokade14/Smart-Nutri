import type { components } from "@smartnutri/api-client";
import type { QueryClient } from "@tanstack/react-query";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type MealIn = components["schemas"]["MealIn"];
export type MealOut = components["schemas"]["MealOut"];
export type Summary = components["schemas"]["Summary"];
export type DaySummary = components["schemas"]["DaySummary"];
export type SummaryPeriod = components["schemas"]["SummaryPeriod"];
export type WeekCounts = components["schemas"]["WeekCounts"];

/** Query keys. Meal logs are personal data: dropped on sign-out. */
export const mealsKey = ["meals"] as const;
export const dayMealsKey = (memberId: string, date: string) =>
  ["meals", "list", memberId, date] as const;
export const summaryKey = (
  memberId: string,
  period: SummaryPeriod,
  date: string,
) => ["meals", "summary", memberId, period, date] as const;
export const weekCountsKey = (date: string) =>
  ["meals", "week_counts", date] as const;

/** POST /v1/meals. A repeated client_id returns the stored log (no duplicate). */
export function logMeal(body: MealIn): Promise<MealOut> {
  const api = getApi(); // a misconfigured base URL is not a network error
  return call(api.POST("/v1/meals", { body }));
}

export async function deleteMeal(mealId: string): Promise<void> {
  const api = getApi();
  await call(
    api.DELETE("/v1/meals/{meal_id}", {
      params: { path: { meal_id: mealId } },
    }),
  );
}

/** GET /v1/meals for one IST day (00:00 to the next 00:00, +05:30). */
export function listMealsForDay(
  memberId: string,
  date: string,
): Promise<MealOut[]> {
  const api = getApi();
  const { from, to } = istDayRange(date);
  return call(
    api.GET("/v1/meals", {
      params: { query: { member_id: memberId, from, to } },
    }),
  );
}

/** GET /v1/meals/summary: totals and bands exactly as the API computed them. */
export function getSummary(
  memberId: string,
  period: SummaryPeriod,
  date: string,
): Promise<Summary> {
  const api = getApi();
  return call(
    api.GET("/v1/meals/summary", {
      params: { query: { member_id: memberId, period, date } },
    }),
  );
}

/** GET /v1/meals/week_counts: the family's counts for the weekly share. */
export function getWeekCounts(date: string): Promise<WeekCounts> {
  const api = getApi();
  return call(
    api.GET("/v1/meals/week_counts", { params: { query: { date } } }),
  );
}

// ---- IST dates (the API's day boundaries are fixed +05:30) -----------------

const IST_OFFSET_MS = 330 * 60_000;
const DATE = /^\d{4}-\d{2}-\d{2}$/;

/** Today's date in India (YYYY-MM-DD). */
export function todayIst(now: Date = new Date()): string {
  return new Date(now.getTime() + IST_OFFSET_MS).toISOString().slice(0, 10);
}

/** `date` plus `days` (calendar arithmetic on a YYYY-MM-DD string). */
export function addDays(date: string, days: number): string {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export function isIsoDate(value: string): boolean {
  return DATE.test(value) && !Number.isNaN(Date.parse(`${value}T00:00:00Z`));
}

/** The IST day as a half-open range of timezone-aware datetimes. */
export function istDayRange(date: string): { from: string; to: string } {
  return {
    from: `${date}T00:00:00+05:30`,
    to: `${addDays(date, 1)}T00:00:00+05:30`,
  };
}

/** Drops every meal log and summary on sign-out. */
export function clearMealsCache(client: QueryClient): void {
  client.removeQueries({ queryKey: mealsKey });
}
