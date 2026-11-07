import type { MemberOut, MemberPatch } from "@/features/members/api/members";
import type {
  GoalSettingsIn,
  GoalSettingsOut,
  NumbersDisplay,
  TargetsPreviewIn,
} from "../api/targets";
import { defaultDirection } from "./directionDefaults";

export const ACTIVITIES = ["sedentary", "light", "moderate", "very"] as const;
export const DIRECTIONS = ["lose", "maintain", "gain"] as const;
export const SEX_REFERENCES = ["female", "male", "average"] as const;
export const NUMBERS_DISPLAYS = ["show", "hide_energy", "hide_all"] as const;
export const SEXES = ["female", "male", "other"] as const;
export type PregnancyAnswer = "yes" | "no" | "prefer_not";
export type SexReference = (typeof SEX_REFERENCES)[number];

export type GuideValues = {
  birth_year: string;
  sex: "" | (typeof SEXES)[number];
  height_cm: string;
  weight_kg: string;
  body_fat_pct: string;
  sex_reference: SexReference | "";
  activity: (typeof ACTIVITIES)[number];
  direction: (typeof DIRECTIONS)[number];
  /** The chosen pace (pct of body weight per week), or null for the API default. */
  rate: number | null;
  target_weight: string;
  /** Starts unanswered: preview and save wait for an explicit answer. */
  pregnancy: PregnancyAnswer | "";
  numbers_display: NumbersDisplay;
};

const text = (n: number | null | undefined) => (n == null ? "" : String(n));

/** Pre-filled from the member and any stored guide settings. */
export function initialValues(
  member: MemberOut | undefined,
  settings: GoalSettingsOut | null | undefined,
): GuideValues {
  return {
    birth_year: text(member?.birth_year),
    sex: member?.sex ?? "",
    height_cm: text(member?.height_cm),
    weight_kg: text(member?.weight_kg),
    body_fat_pct: text(member?.body_fat_pct),
    sex_reference: settings?.sex_reference ?? "",
    activity: settings?.activity_level ?? "light",
    direction: settings?.direction ?? defaultDirection(member?.goal),
    rate: settings?.rate_pct_bw_per_week ?? null,
    target_weight: text(settings?.target_weight_kg),
    pregnancy:
      settings == null ? "" : settings.pregnant_or_breastfeeding ? "yes" : "no",
    numbers_display: settings?.numbers_display ?? "show",
  };
}

/** The pregnancy question has been answered (preview and save need it). */
export function pregnancyAnswered(v: GuideValues): boolean {
  return v.pregnancy !== "";
}

/** A typed number, or null when blank or not a number (sent as unknown, never 0). */
export function parseNumber(raw: string): number | null {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

const asksReference = (v: GuideValues) => v.sex === "" || v.sex === "other";

/** The sex-estimate question applies to "other" and "prefer not to say". */
export function needsSexReference(v: GuideValues): boolean {
  return asksReference(v);
}

function body(v: GuideValues): NonNullable<TargetsPreviewIn["body"]> {
  const year = parseNumber(v.birth_year);
  return {
    birth_year: year === null ? null : Math.trunc(year),
    sex: v.sex === "" ? null : v.sex,
    height_cm: parseNumber(v.height_cm),
    weight_kg: parseNumber(v.weight_kg),
    body_fat_pct: parseNumber(v.body_fat_pct),
  };
}

function settings(v: GuideValues, stored: GoalSettingsOut | null | undefined) {
  const reference = asksReference(v) ? v.sex_reference || "average" : null;
  const target = parseNumber(v.target_weight);
  return {
    direction: v.direction,
    activity_level: v.activity,
    // Maintain has no pace; an omitted pace on lose or gain is the API default.
    rate_pct_bw_per_week: v.direction === "maintain" ? null : v.rate,
    target_weight_kg: target,
    sex_reference: reference,
    // "Prefer not to say" pauses the guide, as yes does (Ruling D15).
    pregnant_or_breastfeeding: v.pregnancy !== "no",
    fat_pct_energy: stored?.fat_pct_energy ?? null,
    energy_mode: "formula" as const,
    numbers_display: v.numbers_display,
    summary_view: stored?.summary_view ?? ("remaining" as const),
  };
}

/** The unsaved body for POST /v1/targets/preview (a sent field overrides the stored one). */
export function previewBody(
  v: GuideValues,
  stored: GoalSettingsOut | null | undefined,
): TargetsPreviewIn {
  const s = settings(v, stored);
  return {
    ...s,
    rate_pct_bw_per_week: s.rate_pct_bw_per_week ?? undefined,
    body: body(v),
  };
}

export function settingsBody(
  v: GuideValues,
  stored: GoalSettingsOut | null | undefined,
): GoalSettingsIn {
  const s = settings(v, stored);
  return { ...s, rate_pct_bw_per_week: s.rate_pct_bw_per_week ?? undefined };
}

/**
 * The members PATCH for the body data. A blank body fat after a stored value
 * clears it (`clear_body_fat_pct`); blank with none stored is left out. A
 * blank year of birth is "unchanged" (the API never clears it).
 */
export function memberPatch(v: GuideValues, stored: MemberOut): MemberPatch {
  const b = body(v);
  return {
    birth_year: b.birth_year ?? null,
    sex: b.sex ?? null,
    height_cm: b.height_cm ?? null,
    weight_kg: b.weight_kg ?? null,
    body_fat_pct: b.body_fat_pct ?? null,
    clear_body_fat_pct: b.body_fat_pct == null && stored.body_fat_pct != null,
  };
}
