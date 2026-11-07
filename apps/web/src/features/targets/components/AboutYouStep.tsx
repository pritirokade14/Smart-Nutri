"use client";

import { useTranslations } from "next-intl";
import { useId } from "react";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import {
  type GuideValues,
  needsSexReference,
  SEX_REFERENCES,
  SEXES,
} from "../lib/guideForm";
import { describedBy, Field } from "./Field";

/**
 * Birth year, sex (with the estimate choice for "other" or "not set"),
 * height, weight and the optional body fat with its explanation (Q10). Blank
 * is unknown, never 0. `highlight` marks the fields the API said are missing;
 * `bodyFatError` is the API's own message.
 */
export function AboutYouStep({
  values,
  onChange,
  highlight = [],
  bodyFatError = null,
}: {
  values: GuideValues;
  onChange: <K extends keyof GuideValues>(k: K, v: GuideValues[K]) => void;
  highlight?: readonly string[];
  bodyFatError?: string | null;
}) {
  const t = useTranslations();
  const ids = useId();
  const id = (f: string) => `${ids}-${f}`;
  const missing = (f: string) => (highlight.includes(f) ? true : undefined);
  const reference = values.sex_reference || "average";
  return (
    <div className="space-y-4" data-testid="step-about">
      <Field id={id("birth_year")} label={t("members.form.birth_year")}>
        <input
          id={id("birth_year")}
          className={inputClass}
          inputMode="numeric"
          maxLength={4}
          value={values.birth_year}
          aria-invalid={missing("birth_year")}
          onChange={(e) => onChange("birth_year", e.target.value)}
        />
      </Field>
      <Field id={id("sex")} label={t("members.form.sex")}>
        <select
          id={id("sex")}
          className={inputClass}
          value={values.sex}
          aria-invalid={missing("sex")}
          onChange={(e) =>
            onChange("sex", e.target.value as GuideValues["sex"])
          }
        >
          <option value="">{t("members.form.not_set")}</option>
          {SEXES.map((s) => (
            <option key={s} value={s}>
              {t(`members.sex.${s}`)}
            </option>
          ))}
        </select>
      </Field>
      {needsSexReference(values) ? (
        <fieldset className="space-y-2" data-testid="sex-reference">
          <legend className={labelClass}>
            {t("targets.sex_reference.title")}
          </legend>
          {SEX_REFERENCES.map((r) => (
            <label key={r} className="flex min-h-11 items-center gap-3 text-md">
              <input
                type="radio"
                name={id("reference")}
                className="size-5"
                checked={reference === r}
                onChange={() => onChange("sex_reference", r)}
              />
              {t(`targets.sex_reference.${r}`)}
            </label>
          ))}
        </fieldset>
      ) : null}
      <Field id={id("height_cm")} label={t("members.form.height_cm")}>
        <input
          id={id("height_cm")}
          className={inputClass}
          inputMode="decimal"
          value={values.height_cm}
          aria-invalid={missing("height_cm")}
          onChange={(e) => onChange("height_cm", e.target.value)}
        />
      </Field>
      <Field id={id("weight_kg")} label={t("members.form.weight_kg")}>
        <input
          id={id("weight_kg")}
          className={inputClass}
          inputMode="decimal"
          value={values.weight_kg}
          aria-invalid={missing("weight_kg")}
          onChange={(e) => onChange("weight_kg", e.target.value)}
        />
      </Field>
      <Field
        id={id("body_fat")}
        label={t("targets.body_fat.label")}
        hint={t("targets.body_fat.hint")}
        error={bodyFatError}
      >
        <input
          id={id("body_fat")}
          className={inputClass}
          inputMode="decimal"
          value={values.body_fat_pct}
          aria-invalid={bodyFatError ? true : undefined}
          aria-describedby={describedBy(
            id("body_fat"),
            true,
            Boolean(bodyFatError),
          )}
          onChange={(e) => onChange("body_fat_pct", e.target.value)}
        />
      </Field>
      <p className={hintClass}>{t("members.form.health_fields_note")}</p>
    </div>
  );
}
