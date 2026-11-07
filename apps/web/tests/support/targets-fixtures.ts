import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { TargetsOut } from "@/features/targets/api/targets";

const ROOT = join(process.cwd(), "../../packages/test-fixtures/targets");

/** A golden GET /v1/targets body (packages/test-fixtures/targets/expected). */
export function targetsFixture(stem: string): TargetsOut {
  return JSON.parse(
    readFileSync(join(ROOT, "expected", `${stem}.json`), "utf8"),
  ) as TargetsOut;
}

/** Stems of the golden TargetsOut bodies (the error cases are left out). */
export function targetsStems(): string[] {
  return readdirSync(join(ROOT, "expected"))
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(/\.json$/, ""))
    .filter((stem) => "status" in targetsFixture(stem))
    .sort();
}

export function directionDefaultsFixture(): Record<string, string> {
  return JSON.parse(
    readFileSync(join(ROOT, "direction_defaults.json"), "utf8"),
  );
}
