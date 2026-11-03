import { readFileSync } from "node:fs";
import { join } from "node:path";
import { createTranslator } from "next-intl";
import { describe, expect, it } from "vitest";
import {
  type ShareTranslator,
  shareResultText,
  shareWeeklyText,
  shareWho,
} from "@/features/share/shareText";
import { resultMessages } from "@/i18n/client-messages";
import {
  analyzeResponse,
  LOCALES,
  MESSAGES,
  type TestLocale,
} from "../../support/analyze-fixtures";

const SHARE = join(process.cwd(), "../../packages/test-fixtures/share");
type Verdict = {
  member_id: string;
  name: string;
  relation: string;
  status: string;
};
const result = JSON.parse(
  readFileSync(join(SHARE, "share_result.sf_biscuit.json"), "utf8"),
) as {
  expected: Record<TestLocale, string>;
  forbidden_substrings: Record<TestLocale, string[]>;
  input: {
    grade: string | null;
    product: string;
    urls: Record<TestLocale, string>;
    verdicts: Verdict[];
  };
};
const weekly = JSON.parse(
  readFileSync(join(SHARE, "share_weekly.week_family.json"), "utf8"),
) as {
  expected: Record<TestLocale, string>;
  input: { scans: number; logged: number; urls: Record<TestLocale, string> };
};

// The share text is built with the same catalogue the result page gets.
const tr = (l: TestLocale) =>
  createTranslator({
    locale: l,
    messages: resultMessages(MESSAGES[l]),
  }) as unknown as ShareTranslator;

/** The fixture's verdicts in the API's VerdictOut field names. */
const verdicts = () =>
  result.input.verdicts.map((v) => ({
    member_name: v.name,
    relation: v.relation,
    status: v.status,
  }));

// Every reason, reason_variant, claim, condition, allergen, diet and alert
// label in the locale: none may ever appear in a share text.
function healthLabels(l: TestLocale): string[] {
  const m = MESSAGES[l] as unknown as Record<string, unknown>;
  const out: string[] = [];
  const walk = (v: unknown) => {
    if (typeof v === "string") out.push(v);
    else if (v && typeof v === "object") Object.values(v).forEach(walk);
  };
  for (const ns of [
    "reason",
    "reason_variant",
    "condition",
    "allergen",
    "alert",
    "claim_reason",
  ])
    walk(m[ns]);
  // Labels too short or too generic to be a leak on their own.
  return out.filter((s) => s.length >= 6 && !s.includes("{"));
}

describe("shareResultText (privacy)", () => {
  it.each(LOCALES)("%s: equals the shared fixture byte for byte", (l) => {
    const text = shareResultText(
      tr(l),
      { grade: result.input.grade, verdicts: verdicts() },
      result.input.product,
      result.input.urls[l],
    );
    expect(text).toBe(result.expected[l]);
  });

  it.each(LOCALES)(
    "%s: contains no condition, allergen or reason text",
    (l) => {
      const text = shareResultText(
        tr(l),
        { grade: result.input.grade, verdicts: verdicts() },
        result.input.product,
        result.input.urls[l],
      ).toLowerCase();
      for (const bad of result.forbidden_substrings[l])
        expect(text).not.toContain(bad.toLowerCase());
      for (const label of healthLabels(l))
        expect(text).not.toContain(label.toLowerCase());
      // Nobody's full name or member id.
      expect(text).not.toContain("patil");
      for (const v of result.input.verdicts)
        expect(text).not.toContain(v.member_id);
    },
  );

  it("built from a real analyze response, it never carries reasons or ids", () => {
    const body = analyzeResponse("sf_biscuit");
    // The golden members are named after their profiles ("Peanut Allergic");
    // real names are the user's own words, so use neutral ones here.
    const named = body.verdicts.map((v, i) => ({
      ...v,
      member_name: `Member${i}`,
    }));
    const text = shareResultText(
      tr("en"),
      { grade: "D", verdicts: named },
      body.product.name ?? "",
      "https://smartnutri.app/en",
    );
    for (const v of body.verdicts) {
      expect(text).not.toContain(v.member_id);
      for (const r of v.reasons) expect(text).not.toContain(r.code);
    }
    for (const label of healthLabels("en"))
      expect(text.toLowerCase()).not.toContain(label.toLowerCase());
  });

  it("ungraded: the ungraded template", () => {
    const text = shareResultText(
      tr("en"),
      { grade: null, verdicts: verdicts().slice(0, 1) },
      "Plain Khakhra",
      "https://smartnutri.app/en",
    );
    expect(text).toBe(
      "Plain Khakhra — not enough label data for a Nutri-Score. Ravi: Avoid. Checked with SmartNutri: https://smartnutri.app/en",
    );
  });

  it("only the members the user chose; none chosen is product only", () => {
    expect(
      shareResultText(
        tr("en"),
        { grade: "D", verdicts: [] },
        "Sugar Free Biscuit",
        "https://smartnutri.app/en",
      ),
    ).toBe(
      "Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri). Checked with SmartNutri: https://smartnutri.app/en",
    );
    expect(
      shareResultText(
        tr("en"),
        { grade: null, verdicts: [] },
        "Plain Khakhra",
        "https://smartnutri.app/en",
      ),
    ).toBe(
      "Plain Khakhra — not enough label data for a Nutri-Score. Checked with SmartNutri: https://smartnutri.app/en",
    );
  });

  it("who: first word of the name, else the relation; an odd status is unknown", () => {
    const t = tr("en");
    expect(
      shareWho(t, { member_name: "  Ravi   Patil ", relation: "parent" }),
    ).toBe("Ravi");
    expect(shareWho(t, { member_name: " ", relation: "spouse" })).toBe(
      "Spouse",
    );
    expect(shareWho(t, { member_name: "", relation: "weird" })).toBe(
      "Family member",
    );
    expect(
      shareResultText(
        t,
        {
          grade: "A",
          verdicts: [
            { member_name: "Riya", relation: "child", status: "great" },
          ],
        },
        "Oats",
        "u",
      ),
    ).toContain("Riya: Label unclear");
  });
});

describe("shareWeeklyText", () => {
  it.each(LOCALES)("%s: equals the shared fixture (counts only)", (l) => {
    expect(
      shareWeeklyText(
        tr(l),
        weekly.input.scans,
        weekly.input.logged,
        weekly.input.urls[l],
      ),
    ).toBe(weekly.expected[l]);
  });
});
