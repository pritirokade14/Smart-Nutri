import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

type Rs = VerdictOut["reasons"][number];
const rs = (
  code: string,
  severity: Rs["severity"],
  params: Record<string, unknown>,
): Rs => ({ code, severity, params });
const synth = (status: string, reasons: Rs[]): VerdictOut => ({
  member_id: "x",
  member_name: "A",
  relation: "other",
  is_primary: false,
  profile_set_up: true,
  status: status as VerdictOut["status"],
  reasons,
});
const codesIn = (testId: string) =>
  [...screen.getByTestId(testId).querySelectorAll("[data-reason-code]")].map(
    (e) => e.getAttribute("data-reason-code"),
  );
const visibleCodes = () => codesIn("visible-reasons");
const collapsedCodes = () => codesIn("collapsed-reasons");
const collapsedHidden = () =>
  screen.getByTestId("collapsed-reasons").hasAttribute("hidden");

describe("VerdictCard details", () => {
  const all = sharedFixtureCases();
  const pick = (name: string) => {
    const c = all.find((x) => x.name === name);
    if (!c) throw new Error(name);
    return c.verdict;
  };

  it("shows the member name, and 'You' for the primary member with no name", () => {
    renderCard(pick("sf_biscuit.diabetic_adult"));
    expect(
      screen.getByRole("heading", { level: 2, name: "Diabetic Adult" }),
    ).toBeTruthy();
    cleanup();
    renderCard({ ...pick("sf_biscuit.diabetic_adult"), member_name: "" });
    expect(
      screen.getByRole("heading", { level: 2, name: MESSAGES.en.result.you }),
    ).toBeTruthy();
    cleanup();
    // No trimming (parity with Android): a whitespace name is shown as sent.
    renderCard({ ...pick("sf_biscuit.diabetic_adult"), member_name: " A " });
    expect(screen.getByRole("heading", { level: 2 }).textContent).toBe(" A ");
  });

  it("the avoid reason is visible; caution reasons sit behind the toggle, in API order", async () => {
    const { container } = renderCard(pick("sf_biscuit.diabetic_adult"));
    const codes = [...container.querySelectorAll("[data-reason-code]")].map(
      (e) => e.getAttribute("data-reason-code"),
    );
    expect(codes).toEqual([
      "misleading_sugar_claim",
      "cardio_risk_high_in",
      "hidden_sugars",
    ]);
    expect(visibleCodes()).toEqual(["misleading_sugar_claim"]);
    expect(collapsedHidden()).toBe(true);
    await userEvent.click(
      screen.getByRole("button", {
        name: MESSAGES.en.verdict.show_all_reasons,
      }),
    );
    expect(collapsedHidden()).toBe(false);
    expect(
      screen.getByRole("button", { name: MESSAGES.en.verdict.hide_reasons }),
    ).toBeTruthy();
  });

  it("collapses duplicate nutrient_missing lines", () => {
    const v: VerdictOut = {
      member_id: "x",
      member_name: "A",
      relation: "other",
      is_primary: false,
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
      relation: "other",
      is_primary: false,
      profile_set_up: true,
      status: "caution",
      reasons: [{ code: "future_rule", severity: "caution", params: {} }],
    };
    const { container } = renderCard(v);
    expect(container.textContent).not.toContain("future_rule");
    expect(
      screen.getByText(MESSAGES.en.verdict.reason_unavailable),
    ).toBeTruthy();
  });

  it("R22 (a): two allergen_contains avoid reasons are both visible", () => {
    renderCard(
      synth("avoid", [
        rs("allergen_contains", "avoid", { allergen: "milk" }),
        rs("allergen_contains", "avoid", { allergen: "peanut" }),
      ]),
    );
    expect(visibleCodes()).toEqual(["allergen_contains", "allergen_contains"]);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("R22 (b): avoid + allergen_unknown (unknown) are both visible", () => {
    renderCard(
      synth("avoid", [
        rs("sugar_high", "avoid", { sugars_g: 20 }),
        rs("allergen_unknown", "unknown", { allergen: "peanut" }),
      ]),
    );
    expect(visibleCodes()).toEqual(["sugar_high", "allergen_unknown"]);
  });

  it("R22 (c): age_unknown + allergen_unknown are both visible", () => {
    renderCard(
      synth("unknown", [
        rs("age_unknown", "unknown", {}),
        rs("allergen_unknown", "unknown", { allergen: "peanut" }),
      ]),
    );
    expect(visibleCodes()).toEqual(["age_unknown", "allergen_unknown"]);
  });

  it("caution-only card shows the first reason without interaction; the rest are collapsed", () => {
    renderCard(
      synth("caution", [
        rs("energy_dense", "caution", { energy_kcal: 500 }),
        rs("nutriscore_low", "caution", { grade: "D" }),
      ]),
    );
    expect(visibleCodes()).toEqual(["energy_dense"]);
    expect(collapsedCodes()).toEqual(["nutriscore_low"]);
    expect(collapsedHidden()).toBe(true);
    cleanup();
    renderCard(
      synth("caution", [rs("energy_dense", "caution", { energy_kcal: 500 })]),
    );
    expect(visibleCodes()).toEqual(["energy_dense"]);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("R22 (d): caution lines are collapsed behind the toggle; an allergen_ caution stays visible", () => {
    renderCard(
      synth("avoid", [
        rs("sugar_high", "avoid", { sugars_g: 20 }),
        rs("energy_dense", "caution", { energy_kcal: 500 }),
        rs("allergen_may_contain", "caution", { allergen: "soy" }),
        rs("nutriscore_low", "caution", { grade: "D" }),
      ]),
    );
    expect(visibleCodes()).toEqual(["sugar_high", "allergen_may_contain"]);
    expect(collapsedCodes()).toEqual(["energy_dense", "nutriscore_low"]);
    expect(collapsedHidden()).toBe(true);
  });

  it("an unrecognised severity is shown, not collapsed; no toggle without a collapsed group", () => {
    renderCard(
      synth("caution", [rs("future_rule", "mystery" as Rs["severity"], {})]),
    );
    expect(visibleCodes()).toEqual(["future_rule"]);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("profile_set_up false shows a neutral note; true does not", () => {
    renderCard({ ...synth("ok", []), profile_set_up: false });
    const note = screen.getByTestId("profile-note");
    expect(note.textContent).toBe(MESSAGES.en.verdict.profile_not_set_up);
    expect(note.className).not.toMatch(/verdict/);
    cleanup();
    renderCard(synth("ok", []));
    expect(screen.queryByTestId("profile-note")).toBeNull();
  });

  it("an unexpected status string renders as unknown (grey), never ok", () => {
    renderCard({
      member_id: "x",
      member_name: "A",
      relation: "other",
      is_primary: false,
      profile_set_up: true,
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
      relation: "other",
      is_primary: false,
      profile_set_up: true,
      status: "ok",
      reasons: [],
    });
    expect(screen.getByText(MESSAGES.en.status.ok)).toBeTruthy();
    expect(container.querySelector("button")).toBeNull();
  });
});

// The card's tone is keyed on data-verdict (the API status) in globals.css.
describe("verdict colours (globals.css)", () => {
  const css = readFileSync(join(process.cwd(), "src/app/globals.css"), "utf8");
  const rule = (status: string) =>
    css.match(
      new RegExp(`(?:^|\\n)\\[data-verdict="${status}"\\]\\s*\\{([^}]*)\\}`),
    )?.[1] ?? "";

  it.each(["ok", "caution", "unknown", "avoid"])(
    "%s maps to its own verdict token",
    (s) => {
      expect(rule(s)).toContain(`var(--color-verdict-${s})`);
    },
  );
  it("unknown is never green, and the default is the unknown grey", () => {
    expect(rule("unknown")).not.toContain("verdict-ok");
    const base = css.match(/(?:^|\n)\[data-verdict\]\s*\{([^}]*)\}/)?.[1] ?? "";
    expect(base).toContain("var(--color-verdict-unknown)");
    expect(base).not.toContain("verdict-ok");
  });
  it("uses no raw hex colours", () => {
    expect(css).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
  });
});
