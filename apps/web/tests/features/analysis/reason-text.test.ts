import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createTranslator } from "next-intl";
import { describe, expect, it } from "vitest";
import {
  reasonKey,
  reasonText,
  type Translator,
} from "@/features/analysis/lib/reasons";
import { resultMessages } from "@/i18n/client-messages";
import {
  analyzeResponse,
  LOCALES,
  MESSAGES,
  type TestLocale,
  type VerdictOut,
} from "../../support/analyze-fixtures";

type Reason = VerdictOut["reasons"][number];

const ROOT = join(process.cwd(), "../../packages/test-fixtures");

// Golden reasons: real ones are looked up in responses/analyze by
// (product, member, reason_index); "synthetic" ones (the engine's golden
// products never emit them) carry their own reason. Every entry in the
// fixture files also stores the reason, so a client can assert from the file.
type Golden =
  | { product: string; member: string; index: number }
  | { product: "synthetic"; member: "synthetic"; index: 0; reason: Reason };

const GOLDEN: Golden[] = [
  { product: "curd", member: "milk_allergic_child", index: 0 }, // allergen_contains
  { product: "no_ingredients", member: "milk_allergic_child", index: 0 }, // allergen_unknown
  { product: "curd", member: "vegan_adult", index: 0 }, // diet + ingredients list
  {
    product: "synthetic",
    member: "synthetic",
    index: 0,
    reason: {
      code: "diet_violation",
      severity: "avoid",
      params: { diet: "veg", ingredients: [], mark: "non_veg" },
    },
  }, // diet mark-only
  { product: "cola", member: "diabetic_adult", index: 0 }, // sugar numbers
  { product: "cola", member: "milk_allergic_child", index: 1 }, // child pct/limit, per_serving
  { product: "no_ingredients", member: "milk_allergic_child", index: 3 }, // child pct/limit, per_100g
  { product: "cola", member: "diabetic_adult", index: 2 }, // carbs basis per_serving
  { product: "sf_biscuit", member: "diabetic_adult", index: 0 }, // claim
  {
    product: "synthetic",
    member: "synthetic",
    index: 0,
    reason: {
      code: "nutrient_missing",
      severity: "unknown",
      params: { nutrient: "sat_fat", rule: "diabetes" },
    },
  }, // nutrient_missing plain
  {
    product: "synthetic",
    member: "synthetic",
    index: 0,
    reason: {
      code: "nutrient_missing",
      severity: "unknown",
      params: { nutrient: "salt", reason: "low_confidence", rule: "bp" },
    },
  }, // nutrient_missing low_confidence
  { product: "namkeen", member: "diabetic_adult", index: 0 }, // cardio_risk_high_in list
  {
    product: "synthetic",
    member: "synthetic",
    index: 0,
    reason: {
      code: "hidden_sugars",
      severity: "caution",
      params: { ingredients: ["maltodextrin", "dextrose", "glucose syrup"] },
    },
  }, // three-item list
  { product: "cola", member: "no_age", index: 0 }, // age_unknown
  { product: "namkeen", member: "bp_parent", index: 0 }, // salt_high
];

function resolve(g: Golden): Reason {
  if ("reason" in g) return g.reason;
  const index = JSON.parse(
    readFileSync(join(ROOT, "responses/index.json"), "utf8"),
  ) as { members: Record<string, string> };
  const verdict = analyzeResponse(g.product).verdicts.find(
    (v) => v.member_id === index.members[g.member],
  );
  const reason = verdict?.reasons[g.index];
  if (!reason) throw new Error(`no golden reason ${g.product}/${g.member}`);
  return reason;
}

function translator(locale: TestLocale): Translator {
  return createTranslator({
    locale,
    messages: resultMessages(MESSAGES[locale]),
  }) as unknown as Translator;
}

function sorted(v: unknown): unknown {
  if (Array.isArray(v)) return v.map(sorted);
  if (v && typeof v === "object")
    return Object.fromEntries(
      Object.entries(v as Record<string, unknown>)
        .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
        .map(([k, x]) => [k, sorted(x)]),
    );
  return v;
}

function build(locale: TestLocale) {
  const t = translator(locale);
  return GOLDEN.map((g) => {
    const reason = resolve(g);
    return {
      key: reasonKey(reason),
      member: g.member,
      product: g.product,
      reason,
      reason_index: g.index,
      text: reasonText(t, reason, locale),
    };
  });
}

const serialise = (v: unknown) => `${JSON.stringify(sorted(v), null, 2)}\n`;

describe("shared reason text (packages/test-fixtures/reason-text)", () => {
  it.each(LOCALES)("%s matches the fixture file exactly", (locale) => {
    const path = join(ROOT, "reason-text", `${locale}.json`);
    const actual = serialise(build(locale));
    // UPDATE_REASON_TEXT=1 pnpm test reason-text rewrites the files; review the diff.
    if (process.env.UPDATE_REASON_TEXT === "1") writeFileSync(path, actual);
    expect(actual).toBe(readFileSync(path, "utf8"));
  });

  it.each(LOCALES)("%s texts are real messages", (locale) => {
    for (const e of build(locale)) {
      expect(e.text, e.key).not.toMatch(/[{}]/);
      expect(e.text, e.key).not.toBe(
        MESSAGES[locale].verdict.reason_unavailable,
      );
    }
  });
});
