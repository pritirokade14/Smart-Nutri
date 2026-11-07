import type { components } from "@smartnutri/api-client";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

type MeOut = components["schemas"]["MeOut"];

let done = false;

/** Test hook: forget that this session already synced. */
export function resetTimezoneSync(): void {
  done = false;
}

/**
 * Sends the browser's time zone (PUT /v1/me/timezone) when it differs from
 * the account's, once per session. A failure sends nothing and is ignored:
 * the account keeps its zone and a zone change never moves a stored date.
 */
export async function syncTimezone(me: MeOut): Promise<void> {
  if (done) return;
  done = true;
  try {
    const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!zone || zone === me.timezone) return;
    await call(getApi().PUT("/v1/me/timezone", { body: { timezone: zone } }));
  } catch {
    // Ignored on purpose.
  }
}

/** GET /v1/me. */
export function getMe(): Promise<MeOut> {
  return call(getApi().GET("/v1/me"));
}
