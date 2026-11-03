import { createTranslator } from "next-intl";
import { describe, expect, it } from "vitest";
import {
  displayReasons,
  reasonKey,
  reasonText,
  type Translator,
} from "@/features/analysis/lib/reasons";
import { resultMessages } from "@/i18n/client-messages";
import {
  LOCALES,
  MESSAGES,
  sharedFixtureCases,
  type TestLocale,
  type VerdictOut,
} from "../../support/analyze-fixtures";

type Reason = VerdictOut["reasons"][number];

function translator(locale: TestLocale, errors: unknown[] = []): Translator {
  // Same namespaces the result page ships to the client.
  return createTranslator({
    locale,
    messages: resultMessages(MESSAGES[locale]),
    onError: (e) => errors.push(e),
  }) as unknown as Translator;
}
const r = (
  code: string,
  params: Record<string, unknown> = {},
  severity: Reason["severity"] = "caution",
): Reason => ({ code, params, severity });

describe("reasonKey (packages/i18n README rule 1)", () => {
  it("uses reason.<code> by default", () => {
    expect(reasonKey(r("sugar_high", { sugars_g: 10 }))).toBe(
      "reason.sugar_high",
    );
  });
  it("nutrient_missing with low_confidence → variant", () => {
    expect(
      reasonKey(
        r("nutrient_missing", { nutrient: "salt", reason: "low_confidence" }),
      ),
    ).toBe("reason_variant.nutrient_missing_low_confidence");
    expect(reasonKey(r("nutrient_missing", { nutrient: "salt" }))).toBe(
      "reason.nutrient_missing",
    );
  });
  it("diet_violation with no ingredients and mark non_veg → mark-only variant", () => {
    expect(
      reasonKey(
        r("diet_violation", { diet: "veg", ingredients: [], mark: "non_veg" }),
      ),
    ).toBe("reason_variant.diet_violation_mark_only");
    expect(
      reasonKey(r("diet_violation", { diet: "veg", mark: "non_veg" })),
    ).toBe("reason_variant.diet_violation_mark_only");
  });
  it("diet_violation with no ingredients and no/other mark → reason_unavailable", () => {
    const en = translator("en");
    for (const params of [
      { diet: "veg", ingredients: [] },
      { diet: "veg" },
      { diet: "veg", ingredients: [], mark: "brown" },
    ]) {
      const reason = r("diet_violation", params, "avoid");
      expect(reasonKey(reason)).toBe("verdict.reason_unavailable");
      expect(reasonText(en, reason, "en")).toBe(
        MESSAGES.en.verdict.reason_unavailable,
      );
    }
  });
  it("diet_violation with ingredients keeps the plain key", () => {
    expect(
      reasonKey(r("diet_violation", { diet: "veg", ingredients: ["egg"] })),
    ).toBe("reason.diet_violation");
  });
});

describe("reasonText", () => {
  const en = translator("en");

  it("maps diet, allergen, claim and nutrient codes through their namespaces", () => {
    expect(
      reasonText(
        en,
        r("diet_violation", { diet: "jain", ingredients: ["onion"] }),
        "en",
      ),
    ).toBe("May not match the Jain diet: onion.");
    expect(
      reasonText(en, r("allergen_contains", { allergen: "milk" }), "en"),
    ).toBe("Contains Milk, which is on your avoid list.");
    expect(
      reasonText(
        en,
        r("misleading_sugar_claim", { claim: "sugar_free" }),
        "en",
      ),
    ).toBe(
      'The pack says "Sugar free", but the label data does not support this claim.',
    );
    expect(
      reasonText(en, r("nutrient_missing", { nutrient: "sat_fat" }), "en"),
    ).toBe(
      "The label does not show saturated fat, so this check could not be done.",
    );
  });

  it("shows an unrecognised allergen and condition as the member wrote them", () => {
    expect(
      reasonText(en, r("allergen_unrecognised", { allergen: "kiwi" }), "en"),
    ).toBe(
      'We can only search the label for the exact word "kiwi". Check the ingredients yourself.',
    );
    expect(
      reasonText(
        en,
        r("condition_unrecognised", { condition: "diabetes" }),
        "en",
      ),
    ).toBe('We do not have guidance for "diabetes" yet.');
  });

  it("maps high_in through nutrient.* and joins lists with ', ' in every locale", () => {
    expect(
      reasonText(
        en,
        r("cardio_risk_high_in", { high_in: ["sat_fat", "salt"] }),
        "en",
      ),
    ).toBe(
      "High in saturated fat, salt. People managing blood sugar are often advised to limit these; check with your doctor.",
    );
    expect(
      reasonText(
        en,
        r("hidden_sugars", { ingredients: ["maltodextrin", "dextrose", "x"] }),
        "en",
      ),
    ).toBe(
      "Contains sugars listed under other names: maltodextrin, dextrose, x.",
    );
    const hi = translator("hi");
    const list = [MESSAGES.hi.nutrient.sat_fat, MESSAGES.hi.nutrient.salt].join(
      ", ",
    );
    expect(
      reasonText(
        hi,
        r("cardio_risk_high_in", { high_in: ["sat_fat", "salt"] }),
        "hi",
      ),
    ).toContain(list);
  });

  it("formats numbers for the locale and keeps basis as a select", () => {
    expect(reasonText(en, r("salt_moderate", { salt_g: 0.9 }), "en")).toBe(
      "Moderate salt: 0.9 g per 100 g/ml.",
    );
    expect(
      reasonText(
        en,
        r("carbs_per_serving_high", { basis: "per_serving", carbs_g: 31.8 }),
        "en",
      ),
    ).toMatch(/^31\.8 g carbohydrate per serving\./);
    const mr = translator("mr");
    expect(
      reasonText(mr, r("salt_moderate", { salt_g: 41.67 }), "mr"),
    ).toContain("41.67");
  });

  it("uses Latin digits in every locale (R21)", () => {
    for (const locale of LOCALES) {
      const text = reasonText(
        translator(locale),
        r("child_salt_high", { salt_g: 2.5 }),
        locale,
      );
      expect(text, locale).toContain("2.5");
      expect(text, locale).not.toMatch(/[\u0966-\u096F]/); // Devanagari digits
    }
  });

  it("an unknown reason code shows verdict.reason_unavailable, never a crash", () => {
    const errors: unknown[] = [];
    const t = translator("en", errors);
    expect(reasonText(t, r("brand_new_rule", {}, "avoid"), "en")).toBe(
      MESSAGES.en.verdict.reason_unavailable,
    );
    expect(errors).toEqual([]);
  });

  it("a reason missing a param falls back instead of leaking the key or {", () => {
    const t = translator("en", []);
    const text = reasonText(t, r("sugar_high", {}, "caution"), "en");
    expect(text).toBe(MESSAGES.en.verdict.reason_unavailable);
  });

  it("variant selection renders in every locale", () => {
    for (const locale of LOCALES) {
      const errors: unknown[] = [];
      const t = translator(locale, errors);
      const low = reasonText(
        t,
        r("nutrient_missing", { nutrient: "salt", reason: "low_confidence" }),
        locale,
      );
      expect(low).toContain(MESSAGES[locale].nutrient.salt);
      const mark = reasonText(
        t,
        r("diet_violation", { diet: "veg", ingredients: [], mark: "non_veg" }),
        locale,
      );
      expect(mark).toContain(MESSAGES[locale].diet.veg);
      expect(errors).toEqual([]);
    }
  });
});

describe("displayReasons (CROSS-PLAN 13)", () => {
  it("collapses duplicate nutrient_missing per nutrient, keeping API order", () => {
    const shown = displayReasons([
      r("nutrient_missing", { nutrient: "salt", rule: "diabetes" }, "unknown"),
      r("sugar_high", { sugars_g: 10 }, "caution"),
      r(
        "nutrient_missing",
        { nutrient: "salt", rule: "hypertension" },
        "unknown",
      ),
      r(
        "nutrient_missing",
        { nutrient: "sugars_g", rule: "diabetes" },
        "unknown",
      ),
    ]);
    expect(shown.map((x) => [x.code, x.params.nutrient ?? null])).toEqual([
      ["nutrient_missing", "salt"],
      ["sugar_high", null],
      ["nutrient_missing", "sugars_g"],
    ]);
  });
  it("keeps a low_confidence and a plain nutrient_missing for the same nutrient", () => {
    const shown = displayReasons([
      r("nutrient_missing", { nutrient: "salt" }, "unknown"),
      r(
        "nutrient_missing",
        { nutrient: "salt", reason: "low_confidence" },
        "unknown",
      ),
      r("nutrient_missing", { nutrient: "salt", rule: "b" }, "unknown"),
      r(
        "nutrient_missing",
        { nutrient: "salt", reason: "low_confidence", rule: "c" },
        "unknown",
      ),
    ]);
    expect(shown.length).toBe(2);
  });
  it("does not re-sort", () => {
    const input = [
      r("hidden_sugars", { ingredients: ["x"] }, "caution"),
      r("allergen_contains", { allergen: "milk" }, "avoid"),
    ];
    expect(displayReasons(input)).toEqual(input);
  });
});

describe("every reason in every golden response renders in en, hi and mr", () => {
  const cases = sharedFixtureCases();
  it.each(LOCALES)("%s", (locale) => {
    const errors: unknown[] = [];
    const t = translator(locale, errors);
    let count = 0;
    for (const c of cases) {
      for (const reason of c.verdict.reasons) {
        const text = reasonText(t, reason, locale);
        count++;
        expect(text, `${c.name} ${reason.code}`).not.toMatch(/[{}]/);
        expect(text, `${c.name} ${reason.code}`).not.toMatch(/^reason/);
        expect(text, `${c.name} ${reason.code}`).not.toMatch(/[\u0966-\u096F]/);
        // A real reason message, not the generic status fallback.
        expect(
          t.has(reasonKey(reason)),
          `${locale} missing ${reasonKey(reason)}`,
        ).toBe(true);
        expect(text.length).toBeGreaterThan(0);
        // Code params come out as labels from the full catalogue.
        const full = MESSAGES[locale] as unknown as Record<
          string,
          Record<string, string>
        >;
        const p = reason.params as Record<string, unknown>;
        for (const ns of ["diet", "allergen", "claim", "nutrient"]) {
          const v = p[ns];
          if (typeof v === "string" && full[ns]?.[v])
            expect(text, `${c.name} ${ns}`).toContain(full[ns][v]);
        }
        if (Array.isArray(p.high_in))
          for (const k of p.high_in)
            expect(text, `${c.name} high_in`).toContain(
              full.nutrient?.[k as string],
            );
      }
    }
    expect(count).toBeGreaterThan(50);
    expect(errors).toEqual([]);
  });
});
