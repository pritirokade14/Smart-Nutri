import type { MemberPatch } from "@/features/members/api/members";
import { byPriority } from "@/features/modes/layouts";
import type {
  FollowUps,
  PrefillChange,
  PrefillSuggestion,
  UserType,
  UserTypesIn,
} from "../api/userTypes";

// Pure helpers for the "What brings you to SmartNutri?" flow (Plan 9, T12).
// Nothing here decides a verdict or changes a member: the picker stores the
// types, and pre-fill changes are applied only after the user ticks them.

export const MAX_TYPES = 3;

/** Tile order on the picker (decision 1). */
export const TILES: readonly UserType[] = [
  "health_condition",
  "family",
  "weight_loss",
  "gym",
  "allergy_diet",
  "eat_better",
];

/** Types that reveal health data: saving them needs health_data (P9 consent rule). */
export const HEALTH_TYPES: ReadonlySet<UserType> = new Set<UserType>([
  "health_condition",
  "weight_loss",
  "allergy_diet",
]);

/** Follow-up fields that are health data. */
export const HEALTH_FOLLOW_UPS = ["conditions", "allergens", "diet"] as const;

/** Which follow-up belongs to which type (weight_loss has none). */
const FOLLOW_UP_FIELDS: Readonly<
  Record<UserType, readonly (keyof FollowUps)[]>
> = {
  health_condition: ["conditions"],
  family: ["family_with"],
  weight_loss: [],
  gym: ["gym_goal"],
  allergy_diet: ["allergens", "diet"],
  eat_better: ["alerts"],
};

export function hasFollowUp(type: UserType): boolean {
  return FOLLOW_UP_FIELDS[type].length > 0;
}

/** The types that get a follow-up section, in safety-first priority order. */
export function followUpTypes(types: readonly UserType[]): UserType[] {
  return byPriority(types).filter(hasFollowUp);
}

const empty = (v: unknown) =>
  v === undefined || v === null || (Array.isArray(v) && v.length === 0);

/**
 * The PUT body: the types in tap order and only the follow-ups of chosen
 * types (the API rejects a follow-up without its type), empty answers dropped.
 */
export function buildBody(
  types: readonly UserType[],
  answers: FollowUps,
): UserTypesIn {
  const follow_ups: FollowUps = {};
  for (const type of types)
    for (const field of FOLLOW_UP_FIELDS[type]) {
      const v = answers[field];
      if (!empty(v)) (follow_ups as Record<string, unknown>)[field] = v;
    }
  return { types: [...types], follow_ups };
}

/** True when saving `body` needs health_data consent first. */
export function needsHealthConsent(body: UserTypesIn): boolean {
  return (
    body.types.some((t) => HEALTH_TYPES.has(t)) ||
    HEALTH_FOLLOW_UPS.some((f) => !empty(body.follow_ups?.[f]))
  );
}

/** The body without health-revealing types and follow-ups (consent declined). */
export function withoutHealth(body: UserTypesIn): UserTypesIn {
  const types = body.types.filter((t) => !HEALTH_TYPES.has(t));
  const rest = { ...(body.follow_ups ?? {}) };
  for (const f of HEALTH_FOLLOW_UPS) delete rest[f];
  return buildBody(types, rest);
}

/** The review step is shown only with something to confirm. */
export function needsReview(prefill: PrefillSuggestion | null): boolean {
  return Boolean(
    prefill && (prefill.changes.length > 0 || prefill.goal_choice?.length),
  );
}

/**
 * Ticked by default only when the user's own follow-up answer asked for it:
 * conditions, allergens, diet and alerts come from follow-ups; a goal only
 * from the gym follow-up. Goals implied by a type alone (weight loss, eating
 * better) start unticked.
 */
export function tickedByDefault(change: PrefillChange): boolean {
  if (change.field === "goal") return change.reason === "gym";
  return true;
}

export type GoalPick = "neither" | NonNullable<MemberPatch["goal"]>;

/**
 * The one members PATCH body from the ticked changes and the goal choice
 * (each value is the FULL new value the API computed), or null when the user
 * confirmed nothing (then no request is sent).
 */
export function confirmedPatch(
  changes: readonly PrefillChange[],
  ticked: ReadonlySet<number>,
  goal: GoalPick,
): MemberPatch | null {
  const patch: Record<string, unknown> = {};
  changes.forEach((c, i) => {
    if (ticked.has(i)) patch[c.field] = c.value;
  });
  if (goal !== "neither") patch.goal = goal;
  return Object.keys(patch).length > 0 ? (patch as MemberPatch) : null;
}
