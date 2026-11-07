import type { TargetsOut } from "../api/targets";

type T = (key: string, values?: Record<string, string | number>) => string;

const FIELD_LABEL: Record<string, string> = {
  birth_year: "members.form.birth_year",
  sex: "members.form.sex",
  height_cm: "members.form.height_cm",
  weight_kg: "members.form.weight_kg",
};

/**
 * The message for a status that has no numbers (null for `ready` and `none`).
 * Never a verdict: neutral information, with no support link.
 */
export function statusMessage(t: T, targets: TargetsOut): string | null {
  switch (targets.status) {
    case "needs_body_data":
      return t("targets.needs_body_data", {
        fields: targets.missing_fields
          .map((f) => (FIELD_LABEL[f] ? t(FIELD_LABEL[f]) : f))
          .join(", "),
      });
    case "not_available_minor":
      return t("targets.minor");
    case "paused_pregnancy":
      return t("targets.pregnancy.paused");
    default:
      return null;
  }
}

/** True when the API hid any group of numbers (the eye toggle or the setting). */
export function anyHidden(
  targets: Pick<TargetsOut, "numbers_hidden">,
): boolean {
  return targets.numbers_hidden.energy || targets.numbers_hidden.macros;
}
