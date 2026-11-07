"use client";

import { useTranslations } from "next-intl";
import { useId } from "react";
import { cn } from "@/lib/cn";
import { ACTIVITIES, type GuideValues } from "../lib/guideForm";

/** Four cards with everyday examples (the hint under each name). */
export function ActivityStep({
  value,
  onChange,
}: {
  value: GuideValues["activity"];
  onChange: (next: GuideValues["activity"]) => void;
}) {
  const t = useTranslations();
  const name = useId();
  return (
    <fieldset className="space-y-2" data-testid="step-activity">
      <legend className="sr-only">{t("targets.step.activity")}</legend>
      {ACTIVITIES.map((a) => (
        <label
          key={a}
          className={cn(
            "flex min-h-11 cursor-pointer items-start gap-3 rounded-md border p-3",
            value === a
              ? "border-brand-primary bg-brand-soft"
              : "border-border-default bg-surface-default",
          )}
        >
          <input
            type="radio"
            name={name}
            className="mt-1 size-5 shrink-0"
            checked={value === a}
            onChange={() => onChange(a)}
          />
          <span className="space-y-0.5">
            <span className="block text-md font-semibold text-text-primary">
              {t(`targets.activity.${a}`)}
            </span>
            <span className="block text-sm text-text-secondary">
              {t(`targets.activity.${a}_hint`)}
            </span>
          </span>
        </label>
      ))}
    </fieldset>
  );
}
