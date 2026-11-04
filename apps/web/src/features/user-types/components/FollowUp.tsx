"use client";

import { useTranslations } from "next-intl";
import { useId } from "react";
import { Card } from "@/components/ui/Card";
import { labelClass } from "@/components/ui/field";
import {
  CANONICAL_ALLERGENS,
  CONDITIONS,
  CUSTOM_ALERTS,
  DIETS,
} from "@/features/members/lib/memberForm";
import { cn } from "@/lib/cn";
import type { FollowUps, UserType } from "../api/userTypes";
import { followUpTypes } from "../lib/flow";

const FAMILY_WITH = ["children", "parents", "partner", "others"] as const;
const GYM_GOALS = ["build_muscle", "lose_fat", "stay_fit"] as const;

export const chipButton =
  "inline-flex min-h-11 cursor-pointer items-center gap-1.5 rounded-full border px-4 text-md font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary";
export const chipOn = "border-brand-primary bg-brand-soft text-brand-primary";
export const chipOff =
  "border-border-default bg-surface-default text-text-primary hover:bg-surface-muted";

function toggle<T>(list: readonly T[] | null | undefined, v: T): T[] {
  const l = list ?? [];
  return l.includes(v) ? l.filter((x) => x !== v) : [...l, v];
}

function Chips<T extends string>({
  legend,
  options,
  value,
  label,
  onChange,
}: {
  legend: string;
  options: readonly T[];
  value: readonly T[] | null | undefined;
  label: (v: T) => string;
  onChange: (next: T[]) => void;
}) {
  return (
    <fieldset className="space-y-3">
      <legend className={labelClass}>{legend}</legend>
      <div className="flex flex-wrap gap-2">
        {options.map((o) => {
          const on = Boolean(value?.includes(o));
          return (
            <button
              key={o}
              type="button"
              aria-pressed={on}
              className={cn(chipButton, on ? chipOn : chipOff)}
              onClick={() => onChange(toggle(value, o))}
            >
              {label(o)}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

function Radios<T extends string>({
  legend,
  options,
  value,
  label,
  onChange,
}: {
  legend: string;
  options: readonly T[];
  value: T | null | undefined;
  label: (v: T) => string;
  onChange: (next: T) => void;
}) {
  const name = useId();
  return (
    <fieldset className="space-y-2">
      <legend className={labelClass}>{legend}</legend>
      {options.map((o) => (
        <label key={o} className="flex min-h-11 items-center gap-3 text-md">
          <input
            type="radio"
            name={name}
            className="size-5"
            checked={value === o}
            onChange={() => onChange(o)}
          />
          {label(o)}
        </label>
      ))}
    </fieldset>
  );
}

/**
 * At most one short follow-up per chosen type, in safety-first priority
 * order (weight loss has none). The answers are stored with the types; they
 * never change a member by themselves (pre-fill is confirmed separately).
 */
export function FollowUp({
  types,
  answers,
  onChange,
  onAddMember,
}: {
  types: readonly UserType[];
  answers: FollowUps;
  onChange: (next: FollowUps) => void;
  /** Family: save, then open "Add a family member". */
  onAddMember?: () => void;
}) {
  const t = useTranslations();
  const set = <K extends keyof FollowUps>(k: K, v: FollowUps[K]) =>
    onChange({ ...answers, [k]: v });
  return (
    <div className="space-y-4">
      {followUpTypes(types).map((type) => (
        <Card
          as="section"
          key={type}
          className="space-y-4"
          data-testid={`follow-up-${type}`}
        >
          <h2 className="text-md font-semibold text-text-secondary">
            {t(`user_types.tile.${type}.title`)}
          </h2>
          {type === "health_condition" ? (
            <Chips
              legend={t("user_types.follow_up.health_condition.question")}
              options={CONDITIONS}
              value={answers.conditions}
              label={(c) => t(`condition.${c}`)}
              onChange={(v) => set("conditions", v)}
            />
          ) : null}
          {type === "family" ? (
            <>
              <Chips
                legend={t("user_types.follow_up.family.question")}
                options={FAMILY_WITH}
                value={answers.family_with}
                label={(w) => t(`user_types.follow_up.family.${w}`)}
                onChange={(v) => set("family_with", v)}
              />
              {onAddMember ? (
                <button
                  type="button"
                  onClick={onAddMember}
                  className="min-h-11 text-md font-semibold text-brand-primary underline-offset-4 hover:underline"
                >
                  {t("members.add")}
                </button>
              ) : null}
            </>
          ) : null}
          {type === "gym" ? (
            <Radios
              legend={t("user_types.follow_up.gym.question")}
              options={GYM_GOALS}
              value={answers.gym_goal}
              label={(g) => t(`user_types.follow_up.gym.${g}`)}
              onChange={(v) => set("gym_goal", v)}
            />
          ) : null}
          {type === "allergy_diet" ? (
            <>
              <Chips
                legend={t(
                  "user_types.follow_up.allergy_diet.allergens_question",
                )}
                options={CANONICAL_ALLERGENS}
                value={answers.allergens}
                label={(a) => t(`allergen.${a}`)}
                onChange={(v) => set("allergens", v)}
              />
              <Radios
                legend={t("user_types.follow_up.allergy_diet.diet_question")}
                options={DIETS}
                value={answers.diet}
                label={(d) => t(`diet.${d}`)}
                onChange={(v) => set("diet", v)}
              />
            </>
          ) : null}
          {type === "eat_better" ? (
            <>
              <Chips
                legend={t("user_types.follow_up.eat_better.question")}
                options={CUSTOM_ALERTS}
                value={answers.alerts}
                label={(a) => t(`alert.${a}`)}
                onChange={(v) => set("alerts", v)}
              />
              <p className="text-sm text-text-secondary">
                {t("user_types.follow_up.eat_better.hint")}
              </p>
            </>
          ) : null}
        </Card>
      ))}
    </div>
  );
}
