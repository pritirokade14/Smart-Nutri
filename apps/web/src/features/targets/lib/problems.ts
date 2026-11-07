import type { ApiError } from "@/lib/api/errors";

type T = {
  (key: string, values?: Record<string, string | number>): string;
  has(key: string): boolean;
};

export type GuideStepId = "intro" | "about" | "activity" | "goal" | "guide";

const num = (v: unknown, fallback: number): number =>
  typeof v === "number" ? v : fallback;

/** The message for a guide error: the API's own limits, never client wording. */
export function problemMessage(t: T, error: ApiError): string {
  const d = error.details;
  switch (error.code) {
    case "body_fat_out_of_range":
      return t("targets.body_fat.out_of_range", {
        min: num(d.min, 3),
        max: num(d.max, 70),
      });
    case "target_weight_too_low":
      return t("targets.target_weight_too_low", { min: num(d.min_kg, 0) });
    case "goal_not_allowed_underweight":
      return t("targets.underweight");
    case "goal_not_allowed_minor":
      return t("targets.minor");
    default: {
      const key = `error.${error.code}`;
      return t.has(key) ? t(key) : t("error.internal_error");
    }
  }
}

/** The step a guide error belongs to, so the user lands on the field. */
export function problemStep(error: ApiError): GuideStepId | null {
  switch (error.code) {
    case "body_fat_out_of_range":
      return "about";
    case "target_weight_too_low":
    case "goal_not_allowed_underweight":
    case "rate_not_allowed":
      return "goal";
    default:
      return null;
  }
}
