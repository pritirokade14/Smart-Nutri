import type { TargetsOut } from "../api/targets";
import { formatInt } from "./format";

type T = {
  (key: string, values?: Record<string, string | number>): string;
  has(key: string): boolean;
};

/**
 * The neutral note for one engine flag, or null for a flag this client does
 * not know. `floor_applied` names the floor only when the API sent it: with
 * hidden numbers `explanation.floor_kcal` is null and the hidden copy is used
 * (no digits).
 */
export function flagMessage(
  t: T,
  flag: string,
  targets: TargetsOut,
): string | null {
  if (flag === "floor_applied") {
    const floor = targets.explanation?.floor_kcal;
    return typeof floor === "number" && !targets.numbers_hidden.energy
      ? t("targets.flag.floor_applied", { value: formatInt(floor) })
      : t("targets.flag.floor_applied_hidden");
  }
  const key = `targets.flag.${flag}`;
  return t.has(key) ? t(key) : null;
}
