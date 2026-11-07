import type { GoalSettingsIn } from "../api/targets";

export type Direction = GoalSettingsIn["direction"];

/**
 * The goal chip's default direction (mirrors
 * packages/test-fixtures/targets/direction_defaults.json). The key is the
 * member's goal, or `none`. The user can change it in the goal step.
 */
export const DIRECTION_FOR_GOAL: Readonly<Record<string, Direction>> = {
  build_muscle: "gain",
  weight_loss: "lose",
  healthy_eating: "maintain",
  weight_gain: "gain",
  none: "maintain",
};

export function defaultDirection(goal: string | null | undefined): Direction {
  return DIRECTION_FOR_GOAL[goal ?? "none"] ?? "maintain";
}
