import type { components } from "@smartnutri/api-client";
import type { QueryClient } from "@tanstack/react-query";
import { getApi } from "@/lib/api/client";
import { networkError, toApiError } from "@/lib/api/errors";

export type MemberOut = components["schemas"]["MemberOut"];
export type MemberIn = components["schemas"]["MemberIn"];
export type MemberPatch = components["schemas"]["MemberPatch"];
export type ConsentState = components["schemas"]["ConsentState"];
export type ConsentIn = components["schemas"]["ConsentIn"];
export type ConsentPurpose = ConsentIn["purpose"];

/** Query keys. Both hold health data: dropped on sign-out (clearMembersCache). */
export const membersKey = ["members"] as const;
export const memberKey = (id: string) => ["members", id] as const;
export const consentsKey = ["consents"] as const;

type Result<T> = {
  data?: T;
  error?: unknown;
  response: Response;
};

// A fetch failure (offline, DNS, CORS) is a network error; an error body is
// the API's envelope, mapped to a stable code.
async function call<T>(p: Promise<Result<T>>): Promise<T> {
  const result = await p.catch(() => {
    throw networkError();
  });
  if (result.error !== undefined) {
    throw toApiError(result.error, result.response.status);
  }
  return result.data as T;
}

/** GET /v1/members: the primary (the account holder) first, then the family. */
export function listMembers(): Promise<MemberOut[]> {
  const api = getApi(); // a misconfigured base URL is not a network error
  return call(api.GET("/v1/members"));
}

export function getMember(id: string): Promise<MemberOut> {
  const api = getApi();
  return call(
    api.GET("/v1/members/{member_id}", { params: { path: { member_id: id } } }),
  );
}

export function createMember(body: MemberIn): Promise<MemberOut> {
  const api = getApi();
  return call(api.POST("/v1/members", { body }));
}

export function updateMember(
  id: string,
  body: MemberPatch,
): Promise<MemberOut> {
  const api = getApi();
  return call(
    api.PATCH("/v1/members/{member_id}", {
      params: { path: { member_id: id } },
      body,
    }),
  );
}

export async function deleteMember(id: string): Promise<void> {
  const api = getApi();
  await call(
    api.DELETE("/v1/members/{member_id}", {
      params: { path: { member_id: id } },
    }),
  );
}

/** GET /v1/consents: always all three purposes, with the current text version. */
export function listConsents(): Promise<ConsentState[]> {
  const api = getApi();
  return call(api.GET("/v1/consents"));
}

/** POST /v1/consents: grant (at the current version) or withdraw one purpose. */
export function recordConsent(body: ConsentIn): Promise<ConsentState[]> {
  const api = getApi();
  return call(api.POST("/v1/consents", { body }));
}

/** True when `purpose` is granted at its current text version. */
export function isGranted(
  states: readonly ConsentState[] | undefined,
  purpose: ConsentPurpose,
): boolean {
  const s = states?.find((c) => c.purpose === purpose);
  return Boolean(s?.granted && s.version === s.current_version);
}

/** Drops members and consents (health data) from the cache on sign-out. */
export function clearMembersCache(client: QueryClient): void {
  client.removeQueries({ queryKey: membersKey });
  client.removeQueries({ queryKey: consentsKey });
}
