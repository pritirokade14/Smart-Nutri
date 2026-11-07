import type { components } from "@smartnutri/api-client";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type WeightOut = components["schemas"]["WeightOut"];
export type WeightsOut = components["schemas"]["WeightsOut"];
export type WeightIn = components["schemas"]["WeightIn"];
export type WeightTrendOut = components["schemas"]["WeightTrendOut"];
export type TrendDays = 30 | 90 | 365;

/**
 * Weights are health data. Their query keys live under ["meals"] so the
 * sign-out purge (clearMealsCache) drops them; they are never sent to
 * analytics.
 */
export const weightsKey = ["meals", "weights"] as const;
export const weightTrendKey = (days: TrendDays) =>
  ["meals", "weights", "trend", days] as const;
export const weightListKey = ["meals", "weights", "list"] as const;

/** GET /v1/weights: the last 90 local days, oldest first (the API's default). */
export function listWeights(): Promise<WeightsOut> {
  const api = getApi();
  return call(api.GET("/v1/weights", { params: { query: {} } }));
}

/** GET /v1/weights/trend: trend, rate and projection, all computed by the API. */
export function getWeightTrend(days: TrendDays): Promise<WeightTrendOut> {
  const api = getApi();
  return call(api.GET("/v1/weights/trend", { params: { query: { days } } }));
}

/** PUT /v1/weights/{day}: creates or replaces the day's weigh-in. */
export function putWeight(day: string, body: WeightIn): Promise<WeightOut> {
  const api = getApi();
  return call(
    api.PUT("/v1/weights/{day}", { params: { path: { day } }, body }),
  );
}

/** DELETE /v1/weights/{day} (terms only). */
export async function deleteWeight(day: string): Promise<void> {
  const api = getApi();
  await call(
    api.DELETE("/v1/weights/{day}", {
      params: { path: { day }, query: {} },
    }),
  );
}

/** DELETE /v1/weights (terms only, no health_data): erases every weigh-in. */
export async function deleteAllWeights(): Promise<void> {
  const api = getApi();
  await call(api.DELETE("/v1/weights", { params: { query: {} } }));
}
