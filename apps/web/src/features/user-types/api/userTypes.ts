import type { components } from "@smartnutri/api-client";
import type { QueryClient } from "@tanstack/react-query";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type UserTypesOut = components["schemas"]["UserTypesOut"];
export type UserTypesIn = components["schemas"]["UserTypesIn"];
export type FollowUps = components["schemas"]["FollowUps"];
export type UserType = UserTypesOut["types"][number];
export type PrefillSuggestion = components["schemas"]["PrefillSuggestion"];
export type PrefillChange = components["schemas"]["PrefillChange"];

/**
 * Query key. The types reveal health interests: dropped on sign-out
 * (clearUserTypesCache) and never sent to analytics (P9-R8).
 */
export const userTypesKey = ["user_types"] as const;

/** GET /v1/me/user-types (no row yet: unanswered, eat_better). */
export function getUserTypes(): Promise<UserTypesOut> {
  const api = getApi(); // a misconfigured base URL is not a network error
  return call(api.GET("/v1/me/user-types"));
}

/**
 * PUT /v1/me/user-types. `types: []` is "Skip for now". A health-revealing
 * type or follow-up without health_data consent is a 403 consent_required.
 * The response's `prefill` is only a suggestion: nothing on the member changes.
 */
export function putUserTypes(body: UserTypesIn): Promise<UserTypesOut> {
  const api = getApi();
  return call(api.PUT("/v1/me/user-types", { body }));
}

/** PATCH /v1/me/user-types/active: the focused mode (needs no consent). */
export function setActiveType(activeType: UserType): Promise<UserTypesOut> {
  const api = getApi();
  return call(
    api.PATCH("/v1/me/user-types/active", {
      body: { active_type: activeType },
    }),
  );
}

export function clearUserTypesCache(client: QueryClient): void {
  client.removeQueries({ queryKey: userTypesKey });
}
