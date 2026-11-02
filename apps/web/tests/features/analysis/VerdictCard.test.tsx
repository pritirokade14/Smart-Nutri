import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it } from "vitest";
import { VerdictCard } from "@/features/analysis/components/VerdictCard";
import { displayReasons } from "@/features/analysis/lib/reasons";
import { resultMessages } from "@/i18n/client-messages";
import {
  type FixtureCase,
  LOCALES,
  MESSAGES,
  sharedFixtureCases,
  type TestLocale,
  type VerdictOut,
} from "../../support/analyze-fixtures";

afterEach(cleanup);

function renderCard(verdict: VerdictOut, locale: TestLocale = "en") {
  const errors: unknown[] = [];
  const utils = render(
    <NextIntlClientProvider
      locale={locale}
      messages={resultMessages(MESSAGES[locale])}
      onError={(e) => errors.push(e)}
    >
      <VerdictCard verdict={verdict} />
    </NextIntlClientProvider>,
  );
  return { ...utils, errors };
}

const cases = sharedFixtureCases().flatMap((c) =>
  LOCALES.map((locale) => ({ ...c, locale, label: `${c.name} [${locale}]` })),
);

describe.each(cases)(
  "VerdictCard $label",
  (c: FixtureCase & {
    locale: TestLocale;
  }) => {
    it("renders the API status text, data-status and every reason", () => {
      const { container, errors } = renderCard(c.verdict, c.locale);
      expect(c.verdict.status).toBe(c.expected.status); // golden agrees with expected/
      const card = screen.getByTestId("verdict-card");
      expect(card.getAttribute("data-status")).toBe(c.expected.status);
      expect(
        within(card).getByText(
          MESSAGES[c.locale].status[c.expected.status as "ok"],
        ),
      ).toBeTruthy();
      expect(container.textContent).not.toMatch(/[{}]/);
      expect(container.textContent).not.toContain("reason.");
      expect(container.querySelectorAll("[data-reason-code]").length).toBe(
        displayReasons(c.verdict.reasons).length,
      );
      expect(errors).toEqual([]);
    });
  },
);

describe("VerdictCard details", () => {
  const all = sharedFixtureCases();
  const pick = (name: string) => {
    const c = all.find((x) => x.name === name);
    if (!c) throw new Error(name);
    return c.verdict;
  };

  it("shows the member name, and 'You' for the primary member with no name", () => {
    renderCard(pick("sf_biscuit.diabetic_adult"));
    expect(screen.getByText("For Diabetic Adult")).toBeTruthy();
    cleanup();
    renderCard({ ...pick("sf_biscuit.diabetic_adult"), member_name: " " });
    expect(
      screen.getByText(
        MESSAGES.en.result.for_member.replace("{name}", MESSAGES.en.result.you),
      ),
    ).toBeTruthy();
  });

  it("top line is the first API reason; the rest are in an expandable list in order", () => {
    const { container } = renderCard(pick("sf_biscuit.diabetic_adult"));
    const codes = [...container.querySelectorAll("[data-reason-code]")].map(
      (e) => e.getAttribute("data-reason-code"),
    );
    expect(codes).toEqual([
      "misleading_sugar_claim",
      "cardio_risk_high_in",
      "hidden_sugars",
    ]);
    const details = container.querySelector("details");
    expect(details).not.toBeNull();
    expect(details?.querySelector("summary")?.textContent).toBe(
      'The pack says "Sugar free", but the label data does not support this claim.',
    );
  });

  it("collapses duplicate nutrient_missing lines", () => {
    const v: VerdictOut = {
      member_id: "x",
      member_name: "A",
      profile_set_up: true,
      status: "unknown",
      reasons: [
        {
          code: "nutrient_missing",
          severity: "unknown",
          params: { nutrient: "salt", rule: "a" },
        },
        {
          code: "nutrient_missing",
          severity: "unknown",
          params: { nutrient: "salt", rule: "b" },
        },
      ],
    };
    const { container } = renderCard(v);
    expect(container.querySelectorAll("[data-reason-code]").length).toBe(1);
  });

  it("an unknown reason code renders a generic line, never crashes", () => {
    const v: VerdictOut = {
      member_id: "x",
      member_name: "A",
      profile_set_up: true,
      status: "caution",
      reasons: [{ code: "future_rule", severity: "caution", params: {} }],
    };
    const { container } = renderCard(v);
    expect(container.textContent).not.toContain("future_rule");
    expect(screen.getAllByText(MESSAGES.en.status.caution).length).toBe(2);
  });

  it("an unexpected status string renders as unknown (grey), never ok", () => {
    renderCard({
      member_id: "x",
      member_name: "A",
      status: "safe" as VerdictOut["status"],
      reasons: [],
    });
    const card = screen.getByTestId("verdict-card");
    expect(card.getAttribute("data-status")).toBe("unknown");
    expect(within(card).getByText(MESSAGES.en.status.unknown)).toBeTruthy();
    expect(within(card).queryByText(MESSAGES.en.status.ok)).toBeNull();
  });

  it("a status with no reasons renders just the status", () => {
    const { container } = renderCard({
      member_id: "x",
      member_name: "A",
      profile_set_up: true,
      status: "ok",
      reasons: [],
    });
    expect(screen.getByText(MESSAGES.en.status.ok)).toBeTruthy();
    expect(container.querySelector("details")).toBeNull();
  });
});

describe("verdict colours (globals.css)", () => {
  const css = readFileSync(join(process.cwd(), "src/app/globals.css"), "utf8");
  const rule = (status: string) =>
    css.match(
      new RegExp(
        `\\.verdict-card\\[data-status="${status}"\\]\\s*\\{([^}]*)\\}`,
      ),
    )?.[1] ?? "";

  it.each(["ok", "caution", "unknown", "avoid"])(
    "%s maps to its own verdict token",
    (s) => {
      expect(rule(s)).toContain(`var(--color-verdict-${s})`);
    },
  );
  it("unknown is never green, and the default is the unknown grey", () => {
    expect(rule("unknown")).not.toContain("verdict-ok");
    const base = css.match(/\.verdict-card\s*\{([^}]*)\}/)?.[1] ?? "";
    expect(base).toContain("var(--color-verdict-unknown)");
    expect(base).not.toContain("verdict-ok");
  });
  it("uses no raw hex colours", () => {
    expect(css).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });
});
