import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type {
  Basis,
  Category,
  ConfirmableField,
  ProductCreate,
  ProductDraft,
  ScanDraftOut,
  SodiumUnit,
} from "@/features/scan/lib/draftSchema";

/**
 * The shared confirm-screen drafts (packages/test-fixtures/drafts), generated
 * by the API from real `to_draft` output. Read from the repo, never copied.
 */
export const DRAFTS_DIR = join(
  process.cwd(),
  "../../packages/test-fixtures/drafts",
);

export type DraftCase =
  | "clean"
  | "basis_mismatch_both_columns"
  | "basis_mismatch_one_column"
  | "derived_from_serving"
  | "per_serving_only_no_serving"
  | "derived_basis_mismatch"
  | "unit_unconfirmed_sodium_per_100g"
  | "unit_unconfirmed_sodium_per_serving"
  | "upper_bound_protein_per_100g"
  | "upper_bound_protein_per_serving"
  | "category_check"
  | "category_unknown"
  | "low_confidence"
  | "implausible_value"
  | "devanagari";

export const SCAN_ID = "0b6c1f8e-3c1a-4f0e-9a51-1d2e3f4a5b6c";

const readJson = (file: string): unknown =>
  JSON.parse(readFileSync(join(DRAFTS_DIR, file), "utf8"));

/** Every `<case>.json` in the shared folder (expected.json excluded). */
export function draftCaseFiles(): string[] {
  return readdirSync(DRAFTS_DIR)
    .filter((f) => f.endsWith(".json") && f !== "expected.json")
    .sort();
}

export function draftFile(file: string): ProductDraft {
  return readJson(file) as ProductDraft;
}

export function draft(name: DraftCase): ProductDraft {
  return draftFile(`${name}.json`);
}

/** A POST /v1/scans/label response wrapping a shared draft. */
export function scanDraft(name: DraftCase): ScanDraftOut {
  return {
    scan_id: SCAN_ID,
    cached: false,
    prompt_version: "label-extract-v3",
    draft: draft(name),
  };
}

export type ScriptedActions = {
  pick_basis?: Basis;
  pick_category?: Category;
  tick?: ConfirmableField[];
  sodium_unit?: SodiumUnit;
  edit?: Record<string, number | null>;
};

export type ScriptedSave = {
  actions: ScriptedActions;
  /** ProductCreate without scan_id (and no barcode). */
  body: Omit<ProductCreate, "scan_id" | "barcode">;
  result:
    | { status: 201; stored: unknown }
    | { status: 422; error: { code: string; fields: string[] } };
};

export type ExpectedDrafts = {
  format_version: number;
  cases: Record<
    string,
    { description: string; draft: string; saves: ScriptedSave[] }
  >;
};

export function expectedDrafts(): ExpectedDrafts {
  return readJson("expected.json") as ExpectedDrafts;
}

export const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

export const envelope = (code: string, details: object = {}) => ({
  error: { code, message_key: `error.${code}`, details },
});
