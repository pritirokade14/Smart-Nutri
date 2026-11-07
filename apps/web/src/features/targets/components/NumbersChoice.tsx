"use client";

import { useTranslations } from "next-intl";
import { useId } from "react";
import { labelClass } from "@/components/ui/field";
import type { NumbersDisplay } from "../api/targets";
import { NUMBERS_DISPLAYS } from "../lib/guideForm";

/** How to see numbers: show (preselected), hide calories or hide all (Q7). */
export function NumbersChoice({
  value,
  onChange,
}: {
  value: NumbersDisplay;
  onChange: (next: NumbersDisplay) => void;
}) {
  const t = useTranslations();
  const name = useId();
  return (
    <fieldset className="space-y-2" data-testid="numbers-choice">
      <legend className={labelClass}>
        {t("settings.diary.numbers.title")}
      </legend>
      {NUMBERS_DISPLAYS.map((n) => (
        <label key={n} className="flex min-h-11 items-center gap-3 text-md">
          <input
            type="radio"
            name={name}
            className="size-5"
            checked={value === n}
            onChange={() => onChange(n)}
          />
          {t(`settings.diary.numbers.${n}`)}
        </label>
      ))}
      {value !== "show" ? (
        <p className="text-sm text-text-secondary">
          {t("settings.diary.numbers.hide_note")}
        </p>
      ) : null}
    </fieldset>
  );
}
