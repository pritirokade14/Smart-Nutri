import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { WeightTrendOut } from "@/features/weights/api/weights";

const DIR = join(
  process.cwd(),
  "../../packages/test-fixtures/weights/expected",
);

/** A golden GET /v1/weights/trend body (packages/test-fixtures/weights/expected). */
export function weightTrend(
  stem: string,
  edit?: (d: WeightTrendOut) => void,
): WeightTrendOut {
  const d = {
    member_id: "a0000000-0000-4000-8000-000000000001",
    days: 90,
    from: "2026-01-01",
    to: "2026-01-31",
    ...JSON.parse(readFileSync(join(DIR, `${stem}.json`), "utf8")),
  } as WeightTrendOut;
  edit?.(d);
  return d;
}

export const WEIGHT_STEMS = [
  "gap_calendar_days",
  "hide_all",
  "no_target",
  "projection_after_gap",
  "projection_moving_away",
  "projection_reached",
  "projection_ready",
  "projection_too_far",
  "projection_too_few",
  "rapid_loss_three_weeks",
  "rate_after_gap",
  "single_outlier",
  "step_change_two_in_a_row",
  "three_constant",
  "too_few_for_rate",
  "weekly_rate_loss",
] as const;
