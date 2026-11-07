"use client";

import { useTranslations } from "next-intl";
import { useId } from "react";
import { inputClass, labelClass } from "@/components/ui/field";
import { cn } from "@/lib/cn";
import type { RateOut } from "../api/targets";
import { formatRate } from "../lib/format";
import {
  DIRECTIONS,
  type GuideValues,
  type PregnancyAnswer,
} from "../lib/guideForm";
import { Field } from "./Field";

const PREGNANCY: readonly PregnancyAnswer[] = ["no", "yes", "prefer_not"];

/**
 * Direction (defaulted from the goal chip), the pace chips, an optional target
 * weight and the pregnancy question. The pace chips show `rate_options`
 * exactly as `targets_preview` computed them: kg is never worked out here.
 */
export function GoalStep({
  values,
  onChange,
  rateOptions,
  selectedRate,
  notice = null,
  targetWeightError = null,
}: {
  values: GuideValues;
  onChange: <K extends keyof GuideValues>(k: K, v: GuideValues[K]) => void;
  rateOptions: readonly RateOut[];
  /** The pace in use (the chosen one, else the API's default), for the chip state. */
  selectedRate: number | null;
  notice?: string | null;
  targetWeightError?: string | null;
}) {
  const t = useTranslations();
  const ids = useId();
  const name = (f: string) => `${ids}-${f}`;
  return (
    <div className="space-y-5" data-testid="step-goal">
      {notice ? (
        <p role="status" className="text-md font-medium text-text-primary">
          {notice}
        </p>
      ) : null}
      <fieldset className="space-y-2">
        <legend className={labelClass}>{t("targets.title")}</legend>
        {DIRECTIONS.map((d) => (
          <label key={d} className="flex min-h-11 items-center gap-3 text-md">
            <input
              type="radio"
              name={name("direction")}
              className="size-5"
              checked={values.direction === d}
              onChange={() => {
                onChange("direction", d);
                onChange("rate", null);
              }}
            />
            {t(`targets.direction.${d}`)}
          </label>
        ))}
      </fieldset>
      {values.direction !== "maintain" && rateOptions.length > 0 ? (
        <fieldset className="space-y-2" data-testid="rate-options">
          <legend className={labelClass}>{t("targets.rate_title")}</legend>
          <div className="flex flex-wrap gap-2">
            {rateOptions.map((o) => {
              const on = selectedRate === o.pct_bw_per_week;
              return (
                <button
                  key={o.pct_bw_per_week}
                  type="button"
                  aria-pressed={on}
                  data-testid="rate-chip"
                  className={cn(
                    "inline-flex min-h-11 cursor-pointer items-center rounded-full border px-4 text-md font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
                    on
                      ? "border-brand-primary bg-brand-soft text-brand-primary"
                      : "border-border-default bg-surface-default text-text-primary hover:bg-surface-muted",
                  )}
                  onClick={() => onChange("rate", o.pct_bw_per_week)}
                >
                  {/* kg_per_week is null under hide_all: percent only */}
                  {o.kg_per_week == null
                    ? t("targets.rate_option_pct", {
                        pct: formatRate(o.pct_bw_per_week),
                      })
                    : t("targets.rate_option", {
                        kg: formatRate(o.kg_per_week),
                        pct: formatRate(o.pct_bw_per_week),
                      })}
                </button>
              );
            })}
          </div>
        </fieldset>
      ) : null}
      <Field
        id={name("target")}
        label={t("targets.target_weight")}
        error={targetWeightError}
      >
        <input
          id={name("target")}
          className={inputClass}
          inputMode="decimal"
          value={values.target_weight}
          aria-invalid={targetWeightError ? true : undefined}
          onChange={(e) => onChange("target_weight", e.target.value)}
        />
      </Field>
      <fieldset className="space-y-2">
        <legend className={labelClass}>
          {t("targets.pregnancy.question")}
        </legend>
        {PREGNANCY.map((p) => (
          <label key={p} className="flex min-h-11 items-center gap-3 text-md">
            <input
              type="radio"
              name={name("pregnancy")}
              className="size-5"
              checked={values.pregnancy === p}
              onChange={() => onChange("pregnancy", p)}
            />
            {t(
              p === "prefer_not"
                ? "targets.pregnancy.prefer_not"
                : `targets.pregnancy.${p}`,
            )}
          </label>
        ))}
      </fieldset>
    </div>
  );
}
