import type { components } from "@smartnutri/api-client";
import raw from "../../../../../packages/test-fixtures/modes/layouts.json";

// The focused-mode table (Plan 9, decision 7). The single source of truth is
// packages/test-fixtures/modes/layouts.json (hand-written and reviewed); this
// module imports it and only narrows its types, so a change there reaches the
// web app with no second copy to drift. Android mirrors the same file.
// Presentation only: a mode never changes a verdict, an allergy check or scan.

export type UserType = components["schemas"]["UserTypesOut"]["active_type"];

export const DESTINATIONS = [
  "home",
  "scan",
  "diary",
  "family",
  "protein",
  "compare",
  "search",
  "profile",
  "how_we_score",
] as const;
export type Destination = (typeof DESTINATIONS)[number];

export const HOME_CARDS = [
  "allergy_check",
  "today_targets",
  "today_sugar_salt",
  "today_protein",
  "protein_swaps",
  "protein_claims_tip",
  "claims_tip",
  "not_covered",
  "family_strip",
  "weekly_family",
  "unknown_explainer",
  "custom_alerts_setup",
  "recent_scans",
] as const;
export type HomeCard = (typeof HOME_CARDS)[number];

export type ModeLayout = {
  tabs: readonly Destination[];
  home_cards: readonly HomeCard[];
};

export type ModeTable = {
  priority: readonly UserType[];
  default_type: UserType;
  destinations: readonly Destination[];
  always_first_card_when_any_member_has_allergens: HomeCard;
  modes: Readonly<Record<UserType, ModeLayout>>;
};

const USER_TYPES: readonly UserType[] = [
  "health_condition",
  "family",
  "weight_loss",
  "gym",
  "allergy_diet",
  "eat_better",
];

function check<T extends string>(
  values: readonly string[],
  allowed: readonly T[],
  what: string,
): T[] {
  for (const v of values)
    if (!(allowed as readonly string[]).includes(v))
      throw new Error(`layouts.json: unknown ${what} "${v}"`);
  return values as T[];
}

/** Narrows the JSON; an unknown key fails loudly at load (and in the tests). */
export function parseModeTable(json: typeof raw): ModeTable {
  const modes = {} as Record<UserType, ModeLayout>;
  for (const type of USER_TYPES) {
    const m = (json.modes as Record<string, ModeLayout | undefined>)[type];
    if (!m) throw new Error(`layouts.json: missing mode "${type}"`);
    modes[type] = {
      tabs: check(m.tabs, DESTINATIONS, "destination"),
      home_cards: check(m.home_cards, HOME_CARDS, "home card"),
    };
  }
  return {
    priority: check(json.priority, USER_TYPES, "user type"),
    default_type: check([json.default_type], USER_TYPES, "user type")[0],
    destinations: check(json.destinations, DESTINATIONS, "destination"),
    always_first_card_when_any_member_has_allergens: check(
      [json.always_first_card_when_any_member_has_allergens],
      HOME_CARDS,
      "home card",
    )[0],
    modes,
  };
}

export const MODE_TABLE: ModeTable = parseModeTable(raw);
export const TYPE_PRIORITY = MODE_TABLE.priority;
export const DEFAULT_TYPE = MODE_TABLE.default_type;

/** The five tabs of a mode (scan is always second, profile last). */
export function tabsFor(mode: UserType): readonly Destination[] {
  return MODE_TABLE.modes[mode].tabs;
}

/** "More": every destination not in the mode's bar, in destinations order. */
export function moreFor(mode: UserType): Destination[] {
  const tabs = new Set(tabsFor(mode));
  return MODE_TABLE.destinations.filter((d) => !tabs.has(d));
}

/**
 * The Home cards in order. When any member has an allergen, `allergy_check`
 * comes first in every mode (P9-R7); otherwise only where the mode lists it.
 */
export function homeCardsFor(
  mode: UserType,
  anyMemberHasAllergens: boolean,
): HomeCard[] {
  const first = MODE_TABLE.always_first_card_when_any_member_has_allergens;
  const cards = MODE_TABLE.modes[mode].home_cards.filter((c) => c !== first);
  const listed = MODE_TABLE.modes[mode].home_cards.includes(first);
  return anyMemberHasAllergens || listed ? [first, ...cards] : cards;
}

/** The chosen types sorted by safety-first priority (P9-R4). */
export function byPriority(types: readonly UserType[]): UserType[] {
  return TYPE_PRIORITY.filter((t) => types.includes(t));
}

/** Route path (after the locale) of each destination. */
export const DESTINATION_PATH: Readonly<Record<Destination, string>> = {
  home: "home",
  scan: "scan",
  // The Diary opens the existing History page at /history until Plan 11 Task 11 replaces it.
  diary: "history",
  family: "family",
  protein: "protein",
  compare: "compare",
  search: "search",
  profile: "profile",
  how_we_score: "how-we-score",
};
