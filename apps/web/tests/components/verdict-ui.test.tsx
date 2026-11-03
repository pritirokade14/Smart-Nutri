import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it } from "vitest";
import { NutriScoreChip } from "@/components/ui/NutriScoreChip";
import { ReasonList } from "@/components/ui/ReasonList";
import { VerdictBadge } from "@/components/ui/VerdictBadge";
import { VerdictCard } from "@/features/analysis/components/VerdictCard";
import { resultMessages } from "@/i18n/client-messages";
import {
  LOCALES,
  MESSAGES,
  sharedFixtureCases,
  type TestLocale,
} from "../support/analyze-fixtures";

afterEach(cleanup);

const STATUSES = ["ok", "caution", "unknown", "avoid"] as const;
const ICON = {
  ok: "check-circle",
  caution: "alert-triangle",
  avoid: "stop",
  unknown: "question-circle",
} as const;

function withMessages(ui: React.ReactNode, locale: TestLocale = "en") {
  return render(
    <NextIntlClientProvider
      locale={locale}
      messages={resultMessages(MESSAGES[locale])}
    >
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("VerdictBadge", () => {
  it.each(STATUSES.flatMap((s) => LOCALES.map((l) => [s, l] as const)))(
    "%s [%s]: icon plus the engine's status label, never colour alone",
    (status, locale) => {
      withMessages(<VerdictBadge status={status} />, locale);
      const badge = screen.getByTestId("verdict-badge");
      expect(badge.getAttribute("data-verdict")).toBe(status);
      expect(
        within(badge).getByText(MESSAGES[locale].status[status]),
      ).toBeTruthy();
      const icon = badge.querySelector("svg");
      expect(icon?.getAttribute("data-icon")).toBe(ICON[status]);
      expect(icon?.getAttribute("aria-hidden")).toBe("true");
    },
  );

  it("each status has a distinct icon shape", () => {
    expect(new Set(Object.values(ICON)).size).toBe(4);
  });

  it("an unexpected status renders as unknown (grey, question icon), never ok", () => {
    withMessages(<VerdictBadge status={"safe" as never} />);
    const badge = screen.getByTestId("verdict-badge");
    expect(badge.getAttribute("data-verdict")).toBe("unknown");
    expect(badge.textContent).toBe(MESSAGES.en.status.unknown);
    expect(badge.querySelector("svg")?.getAttribute("data-icon")).toBe(
      "question-circle",
    );
  });

  it("unknown is never green: no ok tone anywhere in the unknown badge", () => {
    const { container } = withMessages(<VerdictBadge status="unknown" />);
    const html = container.innerHTML;
    expect(html).not.toMatch(/verdict-ok|verdict-soft-ok|grade-a|grade-b/);
    expect(html).not.toMatch(/data-verdict="ok"/);
  });

  it("shared fixtures: the badge shows exactly the API status", () => {
    for (const c of sharedFixtureCases()) {
      withMessages(<VerdictBadge status={c.verdict.status} />);
      expect(
        screen.getByTestId("verdict-badge").getAttribute("data-verdict"),
      ).toBe(c.expected.status);
      cleanup();
    }
  });
});

describe("VerdictCard tone", () => {
  it.each(sharedFixtureCases().filter((c) => c.expected.status === "unknown"))(
    "$name: unknown card, badge and icon are all the unknown tone",
    (c) => {
      withMessages(<VerdictCard verdict={c.verdict} />);
      const card = screen.getByTestId("verdict-card");
      expect(card.getAttribute("data-verdict")).toBe("unknown");
      const badge = within(card).getByTestId("verdict-badge");
      expect(badge.getAttribute("data-verdict")).toBe("unknown");
      expect(badge.querySelector("svg")?.getAttribute("data-icon")).toBe(
        "question-circle",
      );
      // Nothing in the card header uses the ok tone.
      const header = card.querySelector("header");
      expect(header?.querySelector('[data-verdict="ok"]')).toBeNull();
    },
  );

  it("an unexpected API status renders the card as unknown, never ok", () => {
    const base = sharedFixtureCases()[0]?.verdict;
    if (!base) throw new Error("no fixtures");
    withMessages(
      <VerdictCard verdict={{ ...base, status: "great" as never }} />,
    );
    const card = screen.getByTestId("verdict-card");
    expect(card.getAttribute("data-verdict")).toBe("unknown");
    expect(within(card).getByText(MESSAGES.en.status.unknown)).toBeTruthy();
  });
});

describe("verdict tone CSS (globals.css)", () => {
  const css = readFileSync(
    join(process.cwd(), "src/app/globals.css"),
    "utf8",
  ).replace(/\/\*[\s\S]*?\*\//g, ""); // drop comments
  // Every rule body that names an ok-tone token, with its selector.
  const rules = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map((m) => ({
    selector: (m[1] ?? "").trim(),
    body: m[2] ?? "",
  }));

  it("the default tone (no or unexpected data-verdict) is the unknown grey", () => {
    const base = rules.find((r) => r.selector === "[data-verdict]");
    expect(base?.body).toMatch(
      /--verdict-color:\s*var\(--color-verdict-unknown\)/,
    );
    expect(base?.body).toMatch(
      /--verdict-soft:\s*var\(--color-verdict-soft-unknown\)/,
    );
  });

  it("unknown maps to the unknown tokens", () => {
    const unknown = rules.find(
      (r) => r.selector === '[data-verdict="unknown"]',
    );
    expect(unknown?.body).toMatch(/var\(--color-verdict-unknown\)/);
    expect(unknown?.body).not.toMatch(/-ok\b/);
  });

  it("the ok (green) tokens are used only by the ok selector and the dark-mode swap", () => {
    const usesOk = rules.filter((r) =>
      /var\(--color-(dark-)?verdict-(soft-)?ok\)/.test(r.body),
    );
    for (const r of usesOk) {
      const darkSwap =
        r.selector === ":root" &&
        /--color-verdict-ok:\s*var\(--color-dark-verdict-ok\)/.test(r.body);
      expect(r.selector === '[data-verdict="ok"]' || darkSwap).toBe(true);
    }
  });

  it("the dark palette swaps unknown to the dark unknown grey", () => {
    expect(css).toMatch(
      /--color-verdict-unknown:\s*var\(--color-dark-verdict-unknown\)/,
    );
    expect(css).toMatch(
      /--color-verdict-soft-unknown:\s*var\(--color-dark-verdict-soft-unknown\)/,
    );
  });
});

describe("ReasonList", () => {
  const items = [
    { key: "a", severity: "avoid", content: "A" },
    { key: "b", severity: "caution", content: "B" },
    { key: "c", severity: "unknown", content: "C" },
    { key: "d", severity: "ok", content: "D" },
    { key: "e", severity: "weird", content: "E" },
  ];

  it("renders every item in order, each with a severity icon", () => {
    render(<ReasonList items={items} testId="reasons" />);
    const list = screen.getByTestId("reasons");
    const rows = [...list.querySelectorAll("li")];
    expect(rows.map((r) => r.textContent)).toEqual(["A", "B", "C", "D", "E"]);
    expect(rows.map((r) => r.getAttribute("data-verdict"))).toEqual([
      "avoid",
      "caution",
      "unknown",
      "ok",
      "unknown", // an unrecognised severity is never shown as ok
    ]);
    expect(
      rows.map((r) => r.querySelector("svg")?.getAttribute("data-icon")),
    ).toEqual([
      "stop",
      "alert-triangle",
      "question-circle",
      "check-circle",
      "question-circle",
    ]);
  });

  it("passes id and hidden through (for a collapsible list)", () => {
    render(<ReasonList items={items} id="x" hidden testId="reasons" />);
    const list = screen.getByTestId("reasons");
    expect(list.id).toBe("x");
    expect(list.hasAttribute("hidden")).toBe(true);
  });
});

describe("NutriScoreChip", () => {
  it.each(["A", "B", "C", "D", "E"])(
    "grade %s: a square letter tile labelled as calculated by SmartNutri",
    (g) => {
      withMessages(<NutriScoreChip grade={g} />);
      const tile = screen.getByTestId("grade-tile");
      expect(tile.textContent).toBe(g);
      expect(tile.getAttribute("role")).toBe("img");
      expect(tile.getAttribute("aria-label")).toBe(`Nutri-Score ${g}`);
      expect(tile.className).toContain(`bg-grade-${g.toLowerCase()}`);
      expect(tile.className).not.toMatch(/verdict/);
      expect(tile.hasAttribute("data-verdict")).toBe(false);
      expect(
        screen.getByText(MESSAGES.en.nutriscore.calculated_by),
      ).toBeTruthy();
    },
  );

  it("no grade (or an unexpected one): the insufficient-data line, no tile", () => {
    withMessages(<NutriScoreChip grade={null} />);
    expect(screen.queryByTestId("grade-tile")).toBeNull();
    expect(
      screen.getByText(MESSAGES.en.nutriscore.insufficient_data),
    ).toBeTruthy();
    cleanup();
    withMessages(<NutriScoreChip grade="Z" />);
    expect(screen.queryByTestId("grade-tile")).toBeNull();
  });
});
