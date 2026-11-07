import { createTranslator } from "next-intl";
import { describe, expect, it } from "vitest";
import { flagMessage } from "@/features/targets/lib/flagMessages";
import { LOCALES, MESSAGES } from "../../support/analyze-fixtures";
import { targetsFixture, targetsStems } from "../../support/targets-fixtures";

const translator = (locale: (typeof LOCALES)[number]) =>
  createTranslator({
    locale,
    messages: MESSAGES[locale],
  }) as unknown as Parameters<typeof flagMessage>[0];

describe("flagMessage", () => {
  for (const locale of LOCALES) {
    it(`every flag in every golden file has a message in ${locale}`, () => {
      const t = translator(locale);
      let seen = 0;
      for (const stem of targetsStems()) {
        const targets = targetsFixture(stem);
        for (const flag of targets.flags) {
          seen += 1;
          const text = flagMessage(t, flag, targets);
          expect(text, `${stem}:${flag}`).toBeTruthy();
          expect(text).not.toContain("targets.flag");
        }
      }
      expect(seen).toBeGreaterThan(5);
    });
  }

  it("floor_applied shows the floor, whole kcal", () => {
    const targets = targetsFixture("g4_floor");
    expect(flagMessage(translator("en"), "floor_applied", targets)).toContain(
      "1,200",
    );
  });

  it("floor_applied with hidden numbers has no digits", () => {
    const targets = targetsFixture("g4_hide_all");
    const text = flagMessage(translator("en"), "floor_applied", targets);
    expect(text).toBeTruthy();
    expect(text).not.toMatch(/\d/);
  });

  it("an unknown flag is null", () => {
    expect(
      flagMessage(
        translator("en"),
        "brand_new",
        targetsFixture("g1_build_muscle"),
      ),
    ).toBeNull();
  });
});
