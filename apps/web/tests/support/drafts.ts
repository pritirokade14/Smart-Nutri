import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { ScanDraftOut } from "@/features/scan/lib/draftSchema";

/** Fixture POST /v1/scans/label responses, one per warning case. */
export type DraftCase =
  | "clean"
  | "basis_mismatch"
  | "unit_unconfirmed_sodium"
  | "unit_unconfirmed_serving_column"
  | "derived_from_serving"
  | "derived_basis_mismatch"
  | "category_check"
  | "upper_bound_protein"
  | "low_confidence"
  | "implausible_value"
  | "devanagari";

const DIR = join(process.cwd(), "tests/support/fixtures/drafts");

export function scanDraft(name: DraftCase): ScanDraftOut {
  return JSON.parse(
    readFileSync(join(DIR, `${name}.json`), "utf8"),
  ) as ScanDraftOut;
}

export const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

export const envelope = (code: string, details: object = {}) => ({
  error: { code, message_key: `error.${code}`, details },
});
