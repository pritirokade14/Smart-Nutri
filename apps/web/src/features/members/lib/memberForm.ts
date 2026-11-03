import type { MemberIn, MemberOut, MemberPatch } from "../api/members";

// Hand-written schema (zod is not a dependency of apps/web; same pattern as
// features/scan/lib/draftSchema.ts). It mirrors MemberIn's limits so the user
// sees mistakes before the request; the API validates again and stays the
// source of truth.

export type NewRelation = MemberIn["relation"];
export type Diet = NonNullable<MemberIn["diet"]>;
export type Sex = NonNullable<MemberIn["sex"]>;
export type Goal = NonNullable<MemberIn["goal"]>;
export type Condition = NonNullable<MemberIn["conditions"]>[number];
export type CustomAlert = NonNullable<MemberIn["custom_alerts"]>[number];

export const RELATIONS: readonly NewRelation[] = [
  "child",
  "parent",
  "spouse",
  "other",
];
export const DIETS: readonly Diet[] = [
  "veg",
  "eggetarian",
  "vegan",
  "jain",
  "non_veg",
];
export const SEXES: readonly Sex[] = ["female", "male", "other"];
export const GOALS: readonly Goal[] = [
  "healthy_eating",
  "weight_loss",
  "weight_gain",
];
export const CONDITIONS: readonly Condition[] = [
  "diabetes",
  "prediabetes",
  "pcos",
  "hypertension",
];
export const CUSTOM_ALERTS: readonly CustomAlert[] = [
  "palm_oil",
  "maida",
  "added_sugar",
  "artificial_sweetener",
  "msg",
];
/** The engine's allergen keys (apps/api allergens.yaml), in display order. */
export const CANONICAL_ALLERGENS = [
  "milk",
  "peanut",
  "gluten",
  "soy",
  "egg",
  "tree_nut",
  "sesame",
  "fish",
  "crustacean",
  "mustard",
  "sulphite",
] as const;

export const NAME_MAX = 40;
export const BIRTH_YEAR_MIN = 1900;
export const MAX_ALLERGENS = 20;
export const ALLERGEN_MIN = 2;
export const ALLERGEN_MAX = 40;
export const HEIGHT = { min: 30, max: 250 } as const;
export const WEIGHT = { min: 2, max: 300 } as const;

/** Raw form state: numbers as typed text, optional selects as "". */
export type MemberFormValues = {
  name: string;
  /** "self" only for the primary member, whose relation can't change. */
  relation: NewRelation | "self" | "";
  birth_year: string;
  sex: Sex | "";
  height_cm: string;
  weight_kg: string;
  diet: Diet;
  allergens: string[];
  conditions: Condition[];
  custom_alerts: CustomAlert[];
  goal: Goal | "";
};

export type MemberField = keyof MemberFormValues;
/** Field → i18n key of the message to show. */
export type MemberFormErrors = Partial<Record<MemberField, string>>;

/** The API body for a create (no relation `self`). */
export type MemberBody = MemberIn;

export function emptyMemberForm(): MemberFormValues {
  return {
    name: "",
    relation: "",
    birth_year: "",
    sex: "",
    height_cm: "",
    weight_kg: "",
    diet: "non_veg",
    allergens: [],
    conditions: [],
    custom_alerts: [],
    goal: "",
  };
}

const text = (n: number | null) => (n === null ? "" : String(n));

export function memberToForm(m: MemberOut): MemberFormValues {
  return {
    name: m.name,
    relation: m.relation,
    birth_year: text(m.birth_year),
    sex: m.sex ?? "",
    height_cm: text(m.height_cm),
    weight_kg: text(m.weight_kg),
    diet: m.diet,
    allergens: [...m.allergens],
    conditions: [...m.conditions],
    custom_alerts: [...m.custom_alerts],
    goal: m.goal ?? "",
  };
}

const chars = (s: string) => [...s].length;

/**
 * One typed allergen as the API stores it: NFC, trimmed, inner spaces
 * collapsed and lower-cased ("Kiwi" → "kiwi"); a canonical key typed in any
 * case is that key. Returns null when it is not 2–40 characters.
 */
export function normaliseAllergen(raw: string): string | null {
  const value = raw.normalize("NFC").trim().replace(/\s+/g, " ").toLowerCase();
  if (chars(value) < ALLERGEN_MIN || chars(value) > ALLERGEN_MAX) return null;
  return value;
}

export function isCanonicalAllergen(a: string): boolean {
  return (CANONICAL_ALLERGENS as readonly string[]).includes(a);
}

const DECIMAL = /^\d+(\.\d+)?$/;

function parseRange(
  raw: string,
  range: { min: number; max: number },
): { ok: boolean; value: number | null } {
  const s = raw.trim();
  if (s === "") return { ok: true, value: null };
  if (!DECIMAL.test(s)) return { ok: false, value: null };
  const n = Number(s);
  return n >= range.min && n <= range.max
    ? { ok: true, value: n }
    : { ok: false, value: null };
}

export type ParseResult =
  | { success: true; data: MemberBody & { relation: MemberOut["relation"] } }
  | { success: false; errors: MemberFormErrors };

/** Validates the form against MemberIn's limits and builds the API body. */
export const memberFormSchema = {
  safeParse(
    values: MemberFormValues,
    currentYear: number = new Date().getFullYear(),
  ): ParseResult {
    const errors: MemberFormErrors = {};
    const name = values.name.trim();
    if (chars(name) < 1 || chars(name) > NAME_MAX)
      errors.name = "members.form.name_invalid";
    if (values.relation === "")
      errors.relation = "members.form.relation_required";
    const year = values.birth_year.trim();
    const birthYear = /^\d{4}$/.test(year) ? Number(year) : Number.NaN;
    if (!(birthYear >= BIRTH_YEAR_MIN && birthYear <= currentYear))
      errors.birth_year = "members.form.birth_year_invalid";
    const height = parseRange(values.height_cm, HEIGHT);
    if (!height.ok) errors.height_cm = "members.form.height_invalid";
    const weight = parseRange(values.weight_kg, WEIGHT);
    if (!weight.ok) errors.weight_kg = "members.form.weight_invalid";

    const allergens: string[] = [];
    for (const a of values.allergens) {
      const n = normaliseAllergen(a);
      if (n === null) {
        errors.allergens = "members.form.allergen_invalid";
        continue;
      }
      if (!allergens.includes(n)) allergens.push(n);
    }
    if (allergens.length > MAX_ALLERGENS)
      errors.allergens = "members.form.allergen_limit";

    if (Object.keys(errors).length > 0) return { success: false, errors };
    return {
      success: true,
      data: {
        name,
        relation: values.relation as NewRelation,
        birth_year: birthYear,
        sex: values.sex === "" ? null : values.sex,
        height_cm: height.value,
        weight_kg: weight.value,
        diet: values.diet,
        allergens,
        conditions: CONDITIONS.filter((c) => values.conditions.includes(c)),
        custom_alerts: CUSTOM_ALERTS.filter((a) =>
          values.custom_alerts.includes(a),
        ),
        goal: values.goal === "" ? null : values.goal,
      },
    };
  },
};

/**
 * The PATCH body: the whole form (so cleared optional fields are cleared),
 * without `relation` for the primary, whose relation can't change.
 */
export function toPatch(body: MemberBody, isPrimary: boolean): MemberPatch {
  const { relation, ...rest } = body;
  return isPrimary ? rest : { ...rest, relation };
}

const adds = (next: readonly string[], prev: readonly string[] = []) =>
  next.some((x) => !prev.includes(x));

/**
 * True when saving writes new health data, which needs an active health_data
 * consent (Ruling P5/P8): a new allergy or condition, or a new goal, height or
 * weight. Pure removals and unchanged values need none. The API checks again
 * (403 consent_required), so this only decides when to ask first.
 */
export function needsHealthConsent(
  body: MemberBody,
  before?: MemberOut,
): boolean {
  const changed = <T>(next: T | null | undefined, prev: T | null | undefined) =>
    next !== null && next !== undefined && next !== prev;
  return (
    adds(body.allergens ?? [], before?.allergens) ||
    adds(body.conditions ?? [], before?.conditions) ||
    changed(body.goal, before?.goal) ||
    changed(body.height_cm, before?.height_cm) ||
    changed(body.weight_kg, before?.weight_kg)
  );
}
