import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { TargetsExplanation } from "@/features/targets/components/TargetsExplanation";
import { MESSAGES } from "../../support/analyze-fixtures";
import { renderIntl } from "../../support/diary-render";

afterEach(cleanup);
const golden = (stem: string) =>
  JSON.parse(
    readFileSync(
      join(
        process.cwd(),
        `../../packages/test-fixtures/targets/expected/${stem}.json`,
      ),
      "utf8",
    ),
  );

describe("targets explanation weight source", () => {
  it("g5_taper_trend says the weight came from the trend", () => {
    const t = golden("g5_taper_trend");
    renderIntl(<TargetsExplanation targets={t} />);
    const li = document.querySelector('[data-line="weight_source"]');
    expect(li?.textContent).toBe(
      MESSAGES.en.targets.how.weight_trend.replace(
        "{value}",
        String(t.explanation.weight_kg_used),
      ),
    );
  });

  it("latest uses the latest copy and hidden numbers have no line", () => {
    const t = golden("g5_taper_trend");
    t.explanation.weight_source = "latest";
    renderIntl(<TargetsExplanation targets={t} />);
    expect(
      document.querySelector('[data-line="weight_source"]')?.textContent,
    ).toContain("latest weigh-in");
    cleanup();
    t.explanation.weight_kg_used = null;
    renderIntl(<TargetsExplanation targets={t} />);
    expect(document.querySelector('[data-line="weight_source"]')).toBeNull();
    expect(screen.queryByText(/Weight used/)).toBeNull();
  });
});
