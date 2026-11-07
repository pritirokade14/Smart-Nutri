import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { DiaryDayOut, DiaryWeekOut } from "@/features/diary/api/diary";

const DIARY = join(
  process.cwd(),
  "../../packages/test-fixtures/diary/expected",
);

/** A golden GET /v1/diary/day body (packages/test-fixtures/diary/expected). */
export function diaryDay(
  stem: string,
  edit?: (d: DiaryDayOut) => void,
): DiaryDayOut {
  const d = JSON.parse(
    readFileSync(join(DIARY, `${stem}.json`), "utf8"),
  ) as DiaryDayOut;
  edit?.(d);
  return d;
}

/** A golden GET /v1/diary/week body. */
export function diaryWeek(
  stem: string,
  edit?: (d: DiaryWeekOut) => void,
): DiaryWeekOut {
  const d = JSON.parse(
    readFileSync(join(DIARY, `${stem}.json`), "utf8"),
  ) as DiaryWeekOut;
  edit?.(d);
  return d;
}

export const DAY_STEMS = [
  "day_archived_slot",
  "day_complete_under",
  "day_consent_required",
  "day_empty",
  "day_half_up",
  "day_hide_all",
  "day_hide_energy",
  "day_incomplete_energy",
  "day_no_target",
  "day_over_energy",
  "day_paused_pregnancy",
  "day_quick_add_kcal_only",
] as const;
