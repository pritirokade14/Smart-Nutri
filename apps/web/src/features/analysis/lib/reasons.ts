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
    return "reason_variant.diet_violation_mark_only";
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
  locale: string,
): Record<string, string> {
  const list = new Intl.ListFormat(locale, { type: "conjunction" });
  // Ruling R21: Latin digits in every locale (packs print Latin digits).
  const num = new Intl.NumberFormat(`${locale}-u-nu-latn`, {
    maximumFractionDigits: 2,
  });
  const values: Record<string, string> = {};
  for (const [k, v] of Object.entries(reason.params ?? {})) {
    if (k === "high_in" && Array.isArray(v)) {
      values[k] = list.format(v.map((c) => label(t, "nutrient", String(c))));
    } else if (k in CODE_PARAM_NAMESPACE && typeof v === "string") {
      values[k] = label(t, CODE_PARAM_NAMESPACE[k] as string, v);
    } else if (Array.isArray(v)) {
      values[k] = list.format(v.map(String));
    } else if (typeof v === "number") {
      values[k] = num.format(v);
    } else if (typeof v === "string" || typeof v === "boolean") {
      values[k] = String(v);
    }
  }
  return values;
}

// TODO(verdict.reason_unavailable): temporary fallback for an unknown reason
// code (the localised severity). Switch to the dedicated key once the
// controller adds it for both clients.
function genericText(t: Translator, severity: string): string {
  const key = `status.${severity}`;
  return t.has(key) ? t(key) : t("status.unknown");
}

/**
 * Localised text for one reason. An unknown code, or a message whose params
 * the API did not send, falls back to the localised severity ("Caution"),
 * never to a raw key or a crash.
 */
export function reasonText(
  t: Translator,
  reason: ReasonOut,
  locale: string,
): string {
  const key = reasonKey(reason);
  const fallback = genericText(t, reason.severity);
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
 * per (nutrient, rule); show one line per missing nutrient (CROSS-PLAN 13).
 */
export function displayReasons(reasons: readonly ReasonOut[]): ReasonOut[] {
  const seen = new Set<string>();
  return reasons.filter((r) => {
    if (r.code !== "nutrient_missing") return true;
    const nutrient = String(r.params?.nutrient ?? "");
    if (seen.has(nutrient)) return false;
    seen.add(nutrient);
    return true;
  });
}

/** The first reason (the API already sorts by severity); "" when none. */
export function topReasonText(
  t: Translator,
  v: VerdictOut,
  locale: string,
): string {
  const [top] = displayReasons(v.reasons);
  return top ? reasonText(t, top, locale) : "";
}
