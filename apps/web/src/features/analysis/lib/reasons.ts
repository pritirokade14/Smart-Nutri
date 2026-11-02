import type { components } from "@smartnutri/api-client";

// Turns the engine's reason codes into text. Follows packages/i18n/README.md
// ("Rendering reasons"). Never changes, drops (except exact duplicate
// nutrient_missing lines) or reorders what the API sent.

export type ReasonOut = components["schemas"]["ReasonOut"];
export type VerdictOut = components["schemas"]["VerdictOut"];

/** The part of a next-intl translator this module uses. */
export type Translator = {
  (key: string, values?: Record<string, string>): string;
  has(key: string): boolean;
};

// Params whose value is a code, and the namespace that labels it. A code with
// no key is shown as-is (an allergen the member typed that we don't recognise).
// {condition} is always the member's own wording, so it is never mapped.
const CODE_PARAM_NAMESPACE: Record<string, string> = {
  diet: "diet",
  allergen: "allergen",
  claim: "claim",
  nutrient: "nutrient",
};
const SAFE_CODE = /^[a-z0-9_]+$/;

/** Rule 1: the message key, including the reason_variant.* cases. */
export function reasonKey(reason: ReasonOut): string {
  const p = reason.params ?? {};
  if (reason.code === "nutrient_missing" && p.reason === "low_confidence") {
    return "reason_variant.nutrient_missing_low_confidence";
  }
  if (
    reason.code === "diet_violation" &&
    !(Array.isArray(p.ingredients) && p.ingredients.length > 0)
  ) {
    // Mark-only wording is valid only for the brown non-veg mark; any other
    // shape is not something the engine emits, so show the generic line.
    return p.mark === "non_veg"
      ? "reason_variant.diet_violation_mark_only"
      : "verdict.reason_unavailable";
  }
  return `reason.${reason.code}`;
}

function label(t: Translator, namespace: string, code: string): string {
  if (!SAFE_CODE.test(code)) return code;
  const key = `${namespace}.${code}`;
  return t.has(key) ? t(key) : code;
}

/** Rules 2–4: code params mapped, lists joined, numbers formatted for the locale. */
export function reasonValues(
  t: Translator,
  reason: ReasonOut,
  _locale: string,
): Record<string, string> {
  // Ruling R22: lists are joined with ", " in every locale (same as Android).
  const join = (items: string[]) => items.join(", ");
  // Latin digits and the English decimal pattern in every locale (same as
  // Android's NumberFormat.decimalPattern('en'): up to 3 fraction digits).
  const num = new Intl.NumberFormat("en", { maximumFractionDigits: 3 });
  const values: Record<string, string> = {};
  for (const [k, v] of Object.entries(reason.params ?? {})) {
    if (k === "high_in" && Array.isArray(v)) {
      values[k] = join(v.map((c) => label(t, "nutrient", String(c))));
    } else if (k in CODE_PARAM_NAMESPACE && typeof v === "string") {
      values[k] = label(t, CODE_PARAM_NAMESPACE[k] as string, v);
    } else if (Array.isArray(v)) {
      values[k] = join(v.map(String));
    } else if (typeof v === "number") {
      values[k] = num.format(v);
    } else if (typeof v === "string" || typeof v === "boolean") {
      values[k] = String(v);
    }
  }
  return values;
}

/**
 * Localised text for one reason. An unknown code, or a message whose params
 * the API did not send, shows verdict.reason_unavailable, never a raw
 * key, a severity label or a crash.
 */
export function reasonText(
  t: Translator,
  reason: ReasonOut,
  locale: string,
): string {
  const key = reasonKey(reason);
  const fallback = t("verdict.reason_unavailable");
  if (!t.has(key)) return fallback;
  let text: string;
  try {
    text = t(key, reasonValues(t, reason, locale));
  } catch {
    return fallback;
  }
  // next-intl returns the key path when formatting fails (e.g. a missing param).
  return text === "" || text === key ? fallback : text;
}

/**
 * The reasons to show, in API order. The engine emits nutrient_missing once
 * per (nutrient, rule); show one line per (nutrient, message key), so a
 * low_confidence variant and a plain one for the same nutrient both appear.
 */
export function displayReasons(reasons: readonly ReasonOut[]): ReasonOut[] {
  const seen = new Set<string>();
  return reasons.filter((r) => {
    if (r.code !== "nutrient_missing") return true;
    const id = `${String(r.params?.nutrient ?? "")}|${reasonKey(r)}`;
    if (seen.has(id)) return false;
    seen.add(id);
    return true;
  });
}

/** Ruling R22: allergen_* and every severity except caution/ok are never collapsed. */
export function isAlwaysVisible(r: ReasonOut): boolean {
  // Only caution and ok may collapse: an unrecognised severity is shown.
  return (
    r.code.startsWith("allergen_") ||
    (r.severity !== "caution" && r.severity !== "ok")
  );
}

/**
 * Visible group first, collapsed group after; API order within each. When no
 * reason is always visible, the first one is shown and the rest collapse.
 */
export function partitionReasons(reasons: readonly ReasonOut[]): {
  visible: ReasonOut[];
  collapsed: ReasonOut[];
} {
  const all = displayReasons(reasons);
  const visible = all.filter(isAlwaysVisible);
  const collapsed = all.filter((r) => !isAlwaysVisible(r));
  // Nothing must-show: lead with the first reason so the card is never bare.
  const first = visible.length === 0 ? collapsed.shift() : undefined;
  if (first) visible.push(first);
  return { visible, collapsed };
}
