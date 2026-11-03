import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, render, screen, within } from "@testing-library/react";
import { createTranslator, NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it } from "vitest";
import { VerdictCard } from "@/features/analysis/components/VerdictCard";
import { reasonText, type Translator } from "@/features/analysis/lib/reasons";
import { resultMessages } from "@/i18n/client-messages";
import {
  LOCALES,
  MESSAGES,
  sharedFixtureCases,
  type TestLocale,
  type VerdictOut,
} from "../../support/analyze-fixtures";

// Task 12: the per-member card over every sf_biscuit member (expected/
// sf_biscuit.*.json), in en, hi and mr: colour from the API status, the
// headline "<status> for <name>", reasons[0] as the leading "why" line, and
// "Label unclear" never green. Same assertions as Android's
// member_verdicts_fixture_test.dart.

afterEach(cleanup);

function renderCard(verdict: VerdictOut, locale: TestLocale) {
  const errors: unknown[] = [];
  render(
    <NextIntlClientProvider
      locale={locale}
      messages={resultMessages(MESSAGES[locale])}
      onError={(e) => errors.push(e)}
    >
      <VerdictCard verdict={verdict} />
    </NextIntlClientProvider>,
  );
  return errors;
}

const translator = (locale: TestLocale) =>
  createTranslator({
    locale,
    messages: resultMessages(MESSAGES[locale]),
  }) as unknown as Translator;

const css = readFileSync(join(process.cwd(), "src/app/globals.css"), "utf8");

const cases = sharedFixtureCases()
  .filter((c) => c.product === "sf_biscuit")
  .flatMap((c) =>
    LOCALES.map((locale) => ({
      ...c,
      locale,
      label: `${c.member} [${locale}]`,
    })),
  );

describe("sf_biscuit per-member verdict cards", () => {
  it("covers every sf_biscuit member", () => {
    expect(new Set(cases.map((c) => c.member)).size).toBe(14);
  });

  it.each(cases)("$label", (c) => {
    const m = MESSAGES[c.locale];
    const errors = renderCard(c.verdict, c.locale);
    const card = screen.getByTestId("verdict-card");
    const status = c.expected.status as keyof typeof m.status;

    // Colour: the API status drives data-verdict → --verdict-color.
    expect(c.verdict.status).toBe(c.expected.status);
    expect(card.getAttribute("data-verdict")).toBe(status);
    expect(card.className).toContain("border-s-(--verdict-color)");
    expect(
      within(card).getByTestId("verdict-badge").getAttribute("data-verdict"),
    ).toBe(status);

    // Headline.
    expect(within(card).getByRole("heading", { level: 2 }).textContent).toBe(
      m.verdict.for_member
        .replace("{status}", m.status[status])
        .replace("{name}", c.verdict.member_name),
    );

    // "Why": reasons[0] leads the visible reasons.
    const reasons = c.verdict.reasons;
    if (reasons.length > 0) {
      const first = within(card)
        .getByTestId("visible-reasons")
        .querySelector("[data-reason-code]");
      expect(first?.getAttribute("data-reason-code")).toBe(reasons[0]?.code);
      expect(first?.textContent).toBe(
        reasonText(translator(c.locale), reasons[0] as never, c.locale),
      );
    } else {
      expect(within(card).queryByTestId("visible-reasons")).toBeNull();
    }

    // "Label unclear" is never green.
    if (status === "unknown") {
      expect(within(card).getByText(m.status.unknown)).toBeTruthy();
      expect(card.getAttribute("data-verdict")).not.toBe("ok");
      expect(card.querySelector('[data-verdict="ok"]')).toBeNull();
    }
    expect(errors).toEqual([]);
  });

  it("the unknown tone maps to the unknown (grey) tokens, never the ok ones", () => {
    const rule = css.match(/\[data-verdict="unknown"\]\s*\{([^}]*)\}/)?.[1];
    expect(rule).toContain("var(--color-verdict-unknown)");
    expect(rule).not.toContain("verdict-ok");
  });

  it("the account holder's card says 'for you'", () => {
    const c = cases.find((x) => x.member === "diabetic_adult");
    if (!c) throw new Error("diabetic_adult");
    renderCard({ ...c.verdict, is_primary: true, member_name: "Asha" }, "hi");
    const m = MESSAGES.hi;
    expect(screen.getByRole("heading", { level: 2 }).textContent).toBe(
      m.verdict.for_you.replace("{status}", m.status.avoid),
    );
  });

  it("an empty name falls back to 'You' in the headline", () => {
    const c = cases.find((x) => x.member === "no_age");
    if (!c) throw new Error("no_age");
    renderCard({ ...c.verdict, member_name: "" }, "en");
    expect(screen.getByRole("heading", { level: 2 }).textContent).toBe(
      MESSAGES.en.verdict.for_member
        .replace("{status}", MESSAGES.en.status.unknown)
        .replace("{name}", MESSAGES.en.result.you),
    );
  });

  it("reasons[0] leads even when a later reason is always visible", () => {
    const v: VerdictOut = {
      member_id: "x",
      member_name: "A",
      relation: "child",
      is_primary: false,
      profile_set_up: true,
      status: "caution",
      reasons: [
        {
          code: "sugar_moderate",
          severity: "caution",
          params: { sugars_g: 8 },
        },
        {
          code: "allergen_may_contain",
          severity: "caution",
          params: { allergen: "soy" },
        },
        {
          code: "energy_dense",
          severity: "caution",
          params: { energy_kcal: 450 },
        },
      ],
    };
    renderCard(v, "en");
    const codes = [
      ...screen
        .getByTestId("visible-reasons")
        .querySelectorAll("[data-reason-code]"),
    ].map((e) => e.getAttribute("data-reason-code"));
    expect(codes).toEqual(["sugar_moderate", "allergen_may_contain"]);
    expect(
      screen
        .getByTestId("collapsed-reasons")
        .querySelector("[data-reason-code]")
        ?.getAttribute("data-reason-code"),
    ).toBe("energy_dense");
  });
});
