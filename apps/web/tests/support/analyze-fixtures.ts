import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { components } from "@smartnutri/api-client";
import en from "@smartnutri/i18n/messages/en.json";
import hi from "@smartnutri/i18n/messages/hi.json";
import mr from "@smartnutri/i18n/messages/mr.json";

export type AnalyzeOut = components["schemas"]["AnalyzeOut"];
export type VerdictOut = components["schemas"]["VerdictOut"];

const ROOT = join(process.cwd(), "../../packages/test-fixtures");
const read = (...p: string[]) =>
  JSON.parse(readFileSync(join(ROOT, ...p), "utf8"));

export const MESSAGES = { en, hi, mr } as const;
export type TestLocale = keyof typeof MESSAGES;
export const LOCALES = Object.keys(MESSAGES) as TestLocale[];

type Index = { members: Record<string, string> };
type Expected = {
  status: string;
  reasons: { code: string; severity: string }[];
};

/** Golden POST /v1/analyze bodies, by product name. */
export function analyzeResponses(): { product: string; body: AnalyzeOut }[] {
  return readdirSync(join(ROOT, "responses/analyze"))
    .filter((f) => f.endsWith(".json"))
    .sort()
    .map((f) => ({
      product: f.replace(/\.json$/, ""),
      body: read("responses/analyze", f) as AnalyzeOut,
    }));
}

export function analyzeResponse(product: string): AnalyzeOut {
  return read("responses/analyze", `${product}.json`) as AnalyzeOut;
}

export type FixtureCase = {
  name: string; // "<product>.<member>"
  product: string;
  member: string;
  verdict: VerdictOut;
  expected: Expected;
};

/** One case per verdict in every golden response, joined to expected/. */
export function sharedFixtureCases(): FixtureCase[] {
  const index = read("responses/index.json") as Index;
  const memberById = new Map(
    Object.entries(index.members).map(([name, id]) => [id, name]),
  );
  const cases: FixtureCase[] = [];
  for (const { product, body } of analyzeResponses()) {
    for (const verdict of body.verdicts) {
      const member = memberById.get(verdict.member_id);
      if (!member) throw new Error(`unknown member_id ${verdict.member_id}`);
      cases.push({
        name: `${product}.${member}`,
        product,
        member,
        verdict,
        expected: read("expected", `${product}.${member}.json`) as Expected,
      });
    }
  }
  return cases;
}
