import type { components } from "@smartnutri/api-client";
import type { QueryClient } from "@tanstack/react-query";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type TargetsOut = components["schemas"]["TargetsOut"];
export type GoalSettingsIn = components["schemas"]["GoalSettingsIn"];
export type GoalSettingsOut = components["schemas"]["GoalSettingsOut"];
export type TargetsPreviewIn = components["schemas"]["TargetsPreviewIn"];
export type DisplayIn = components["schemas"]["DisplayIn"];
export type RateOut = components["schemas"]["RateOut"];
export type TargetsExplanation = components["schemas"]["TargetsExplanation"];
export type NumbersDisplay = NonNullable<GoalSettingsIn["numbers_display"]>;

/**
 * Query keys. Targets and goal settings are health data: dropped on sign-out
 * (clearTargetsCache) and never sent to analytics.
 */
export const targetsKey = ["targets"] as const;
export const todayTargetsKey = ["targets", "today"] as const;
export const goalSettingsKey = ["targets", "settings"] as const;

/** GET /v1/targets (today, the primary member): the engine's numbers as sent. */
export function getTodayTargets(): Promise<TargetsOut> {
  const api = getApi(); // a misconfigured base URL is not a network error
  return call(api.GET("/v1/targets", { params: { query: {} } }));
}

/** GET /v1/targets/settings: null when the member has no daily guide yet. */
export function getGoalSettings(): Promise<GoalSettingsOut | null> {
  const api = getApi();
  return call(api.GET("/v1/targets/settings", { params: { query: {} } }));
}

/** POST /v1/targets/preview: unsaved settings and body data, never stored. */
export function previewTargets(body: TargetsPreviewIn): Promise<TargetsOut> {
  const api = getApi();
  return call(api.POST("/v1/targets/preview", { body }));
}

/** PUT /v1/targets/settings: stores the guide settings, answers today's targets. */
export function putGoalSettings(body: GoalSettingsIn): Promise<TargetsOut> {
  const api = getApi();
  return call(api.PUT("/v1/targets/settings", { body }));
}

/** PUT /v1/targets/display: the eye toggle (terms only, never revalidates). */
export function putDisplay(body: DisplayIn): Promise<GoalSettingsOut> {
  const api = getApi();
  return call(api.PUT("/v1/targets/display", { body }));
}

/** DELETE /v1/targets/settings (idempotent). */
export async function deleteGoalSettings(): Promise<void> {
  const api = getApi();
  await call(api.DELETE("/v1/targets/settings", { params: { query: {} } }));
}

/** Drops every target and setting on sign-out. */
export function clearTargetsCache(client: QueryClient): void {
  client.removeQueries({ queryKey: targetsKey });
}
