import { describe, expect, it } from "vitest";
import { slotLabel } from "@/features/diary/lib/slotLabel";
import { LOCALES, MESSAGES } from "../../support/analyze-fixtures";

const translate = (loc: (typeof LOCALES)[number]) => (key: string) =>
  key
    .split(".")
    .reduce<unknown>(
      (o, k) => (o as Record<string, unknown>)[k],
      MESSAGES[loc],
    ) as string;

describe("slotLabel", () => {
  it.each(LOCALES)("custom label renders exactly as typed in %s", (loc) => {
    expect(
      slotLabel(translate(loc), {
        labelKey: null,
        customLabel: "Evening chai ☕",
      }),
    ).toBe("Evening chai ☕");
  });

  it("a custom label is never translated, even when it looks like a key", () => {
    expect(
      slotLabel(() => "TRANSLATED", {
        labelKey: "diary.slot.lunch",
        customLabel: "diary.slot.breakfast",
      }),
    ).toBe("diary.slot.breakfast");
  });

  it.each(LOCALES)("default key translated in %s", (loc) => {
    expect(
      slotLabel(translate(loc), {
        labelKey: "diary.slot.breakfast",
        customLabel: null,
      }),
    ).toBe(MESSAGES[loc].diary.slot.breakfast);
  });
});
