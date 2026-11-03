import { cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it } from "vitest";
import { ClaimsSection } from "@/features/analysis/components/ClaimsSection";
import { ExplanationCard } from "@/features/analysis/components/ExplanationCard";
import { NutritionTable } from "@/features/analysis/components/NutritionTable";
import {
  type ExplanationOut,
  substituteMembers,
} from "@/features/analysis/lib/explanation";
import { readClaims } from "@/features/analysis/lib/report";
import { resultMessages } from "@/i18n/client-messages";
import {
  analyzeResponse,
  LOCALES,
  MESSAGES,
  type TestLocale,
} from "../../support/analyze-fixtures";

afterEach(cleanup);

function intl(ui: ReactNode, locale: TestLocale = "en") {
  const errors: unknown[] = [];
  const utils = render(
    <NextIntlClientProvider
      locale={locale}
      messages={resultMessages(MESSAGES[locale])}
      onError={(e) => errors.push(e)}
    >
      {ui}
    </NextIntlClientProvider>,
  );
  return { ...utils, errors };
}

const biscuit = analyzeResponse("sf_biscuit");
const verdicts = biscuit.verdicts;
const byName = (name: string) => {
  const v = verdicts.find((x) => x.member_name === name);
  if (!v) throw new Error(name);
  return v;
};

describe("ExplanationCard", () => {
  const dad = byName("Diabetic Adult");
  const kid = byName("Milk Allergic Child");
  const llm = (over: Partial<ExplanationOut> = {}): ExplanationOut => ({
    text: "member_1 should skip this biscuit; member_2 too.",
    tips: ["Pick a biscuit with less sugar for member_1."],
    language: "en",
    source: "llm",
    prompt_version: "explanation_v1",
    member_refs: { member_1: dad.member_id, member_2: kid.member_id },
    ...over,
  });

  it("is hidden when the API says unavailable (the golden responses)", () => {
    expect(biscuit.explanation.source).toBe("unavailable");
    const { container } = intl(
      <ExplanationCard explanation={biscuit.explanation} verdicts={verdicts} />,
    );
    expect(container.innerHTML).toBe("");
    cleanup();
    // Even if text came with it.
    intl(
      <ExplanationCard
        explanation={llm({ source: "unavailable" })}
        verdicts={verdicts}
      />,
    );
    expect(screen.queryByTestId("explanation-card")).toBeNull();
  });

  it.each(LOCALES)(
    "replaces member tokens with names, shows tips and the AI label (%s)",
    (locale) => {
      const m = MESSAGES[locale];
      const { errors } = intl(
        <ExplanationCard explanation={llm()} verdicts={verdicts} />,
        locale,
      );
      const card = screen.getByTestId("explanation-card");
      expect(
        within(card).getByRole("heading", { name: m.explanation.title }),
      ).toBeTruthy();
      expect(within(card).getByTestId("ai-note").textContent).toBe(
        m.explanation.ai_note,
      );
      expect(
        within(card).getByText(
          "Diabetic Adult should skip this biscuit; Milk Allergic Child too.",
        ),
      ).toBeTruthy();
      expect(within(card).getByText(m.explanation.tips_title)).toBeTruthy();
      expect(
        within(card).getByText(
          "Pick a biscuit with less sugar for Diabetic Adult.",
        ),
      ).toBeTruthy();
      expect(card.textContent).not.toMatch(/member_\d/);
      // Neutral: never a verdict colour.
      expect(card.querySelector("[data-verdict]")).toBeNull();
      expect(card.hasAttribute("data-verdict")).toBe(false);
      expect(errors).toEqual([]);
    },
  );

  it("the account holder is 'You'", () => {
    intl(
      <ExplanationCard
        explanation={llm({ text: "member_1 should skip this.", tips: [] })}
        verdicts={verdicts.map((v) =>
          v.member_id === dad.member_id ? { ...v, is_primary: true } : v,
        )}
      />,
    );
    expect(
      screen.getByText(`${MESSAGES.en.result.you} should skip this.`),
    ).toBeTruthy();
    expect(screen.queryByText(MESSAGES.en.explanation.tips_title)).toBeNull();
  });

  it("hides the card when a token can't be resolved", () => {
    for (const bad of [
      llm({ text: "member_3 should skip this." }),
      llm({ tips: ["Ask member_9."] }),
      llm({ member_refs: { member_1: "not-in-this-result" } }),
    ]) {
      intl(<ExplanationCard explanation={bad} verdicts={verdicts} />);
      expect(screen.queryByTestId("explanation-card")).toBeNull();
      cleanup();
    }
  });
});

describe("substituteMembers", () => {
  const names: Record<string, string> = {
    a: "Asha",
    b: "Ravi",
    c: "member_1x",
  };
  const nameOf = (id: string) => names[id] ?? null;

  it("longest token first: member_10 is not member_1 followed by 0", () => {
    const refs: Record<string, string> = { member_1: "a", member_10: "b" };
    expect(substituteMembers("member_10 and member_1.", refs, nameOf)).toBe(
      "Ravi and Asha.",
    );
  });

  it("never substitutes inside an inserted name", () => {
    expect(
      substituteMembers(
        "Hi member_2",
        { member_2: "c", member_1: "a" },
        nameOf,
      ),
    ).toBe("Hi member_1x");
  });

  it("an unmapped token is null; text with no tokens is unchanged", () => {
    expect(
      substituteMembers("member_4 here", { member_1: "a" }, nameOf),
    ).toBeNull();
    expect(substituteMembers("plain text", {}, nameOf)).toBe("plain text");
    expect(substituteMembers("member_1", {}, nameOf)).toBeNull();
  });
});

describe("ClaimsSection", () => {
  it.each(LOCALES)(
    "shows the sf_biscuit sugar-free claim as contradicted, never green (%s)",
    (locale) => {
      const m = MESSAGES[locale];
      const { errors } = intl(
        <ClaimsSection checks={readClaims(biscuit.report)} />,
        locale,
      );
      const section = screen.getByTestId("claims-section");
      expect(
        within(section).getByRole("heading", {
          name: m.product.claims_heading,
        }),
      ).toBeTruthy();
      const row = section.querySelector('[data-claim="sugar_free"]');
      expect(row?.getAttribute("data-claim-verdict")).toBe("contradicted");
      expect(row?.textContent).toContain(
        m.product.label_says.replace("{claim}", m.claim.sugar_free),
      );
      expect(row?.textContent).toContain(m.claim_verdict.contradicted);
      expect(row?.textContent).toContain(
        m.claim_reason.exceeds_limit
          .replace("{value}", "2")
          .replace("{limit}", "0.5"),
      );
      expect(section.querySelector('[data-verdict="ok"]')).toBeNull();
      expect(row?.querySelector('[data-verdict="caution"]')).toBeTruthy();
      expect(errors).toEqual([]);
    },
  );

  it("supported is neutral and unverifiable is grey; unknown claims and bad params are dropped", () => {
    const { container } = intl(
      <ClaimsSection
        checks={readClaims({
          claims: [
            {
              claim: "high_protein",
              verdict: "supported",
              reason_code: "ok",
              params: {},
            },
            {
              claim: "low_fat",
              verdict: "unverifiable",
              reason_code: "nutrient_missing",
              params: { nutrient: "sat_fat" },
            },
            {
              claim: "low_sodium",
              verdict: "contradicted",
              reason_code: "exceeds_limit",
              params: {},
            },
            {
              claim: "mystery_claim",
              verdict: "supported",
              reason_code: "ok",
              params: {},
            },
            {
              claim: "low_sugar",
              verdict: "great",
              reason_code: "ok",
              params: {},
            },
          ],
        })}
      />,
    );
    const rows = [...container.querySelectorAll("[data-claim]")];
    expect(rows.map((r) => r.getAttribute("data-claim"))).toEqual([
      "high_protein",
      "low_fat",
      "low_sodium",
    ]);
    expect(rows[0]?.querySelector("[data-verdict]")).toBeNull();
    expect(rows[1]?.querySelector('[data-verdict="unknown"]')).toBeTruthy();
    expect(rows[1]?.textContent).toContain(
      MESSAGES.en.claim_reason.nutrient_missing.replace(
        "{nutrient}",
        MESSAGES.en.nutrient.sat_fat,
      ),
    );
    // Params that don't fit: the claim and verdict show, no reason line.
    expect(rows[2]?.textContent).toBe(
      MESSAGES.en.product.label_says.replace(
        "{claim}",
        MESSAGES.en.claim.low_sodium,
      ) + MESSAGES.en.claim_verdict.contradicted,
    );
  });

  it("renders nothing with no claims", () => {
    const { container } = intl(<ClaimsSection checks={[]} />);
    expect(container.innerHTML).toBe("");
  });
});

describe("NutritionTable", () => {
  it.each(LOCALES)(
    "shows per-100 g values; a missing one is 'Not on the label', never 0 (%s)",
    (locale) => {
      const m = MESSAGES[locale];
      intl(<NutritionTable per100g={biscuit.product.per_100g} />, locale);
      const table = screen.getByTestId("nutrition-table");
      expect(
        within(table).getByRole("heading", { name: m.result.nutrition_title }),
      ).toBeTruthy();
      const row = (k: string) =>
        table.querySelector(`[data-nutrient="${k}"]`)?.textContent;
      expect(row("energy_kcal")).toBe(`${m.confirm.field.energy_kcal}450`);
      expect(row("salt_g")).toBe(`${m.confirm.field.salt_g}0.9`);
      expect(row("sodium_mg")).toBe(
        `${m.confirm.field.sodium_mg}${m.result.not_on_label}`,
      );
      expect(table.querySelectorAll("[data-nutrient]")).toHaveLength(9);
    },
  );
});
