import type { components } from "@smartnutri/api-client";
import { isErrorEnvelope } from "./errors";

export type ConsentPurpose = components["schemas"]["ConsentIn"]["purpose"];

const PURPOSES: ReadonlySet<string> = new Set<ConsentPurpose>([
  "terms",
  "health_data",
  "ai_processing",
]);

/**
 * The missing purposes of a route-gate 403 (`consent_required` with
 * `details.purposes`, ADR 0018), or null for anything else. The members gate
 * sends a singular `details.purpose`; its form asks for health data itself,
 * so it is not routed here. Never consumes the caller's body.
 */
export async function consentPurposes(
  response: Response,
): Promise<ConsentPurpose[] | null> {
  if (response.status !== 403) return null;
  let body: unknown;
  try {
    body = await response.clone().json();
  } catch {
    return null;
  }
  if (!isErrorEnvelope(body) || body.error.code !== "consent_required")
    return null;
  const purposes = (body.error.details as { purposes?: unknown } | undefined)
    ?.purposes;
  if (!Array.isArray(purposes)) return null;
  const known = purposes.filter(
    (p): p is ConsentPurpose => typeof p === "string" && PURPOSES.has(p),
  );
  return known.length > 0 ? known : null;
}
