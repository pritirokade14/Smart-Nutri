"use client";

import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { labelClass } from "@/components/ui/field";
import { SectionHeader } from "@/components/ui/SectionHeader";
import {
  ConsentDialog,
  errorKey,
} from "@/features/members/components/ConsentDialog";
import { useSaveMember } from "@/features/members/hooks/useMembers";
import { isCanonicalAllergen } from "@/features/members/lib/memberForm";
import type { ApiError } from "@/lib/api/errors";
import type { PrefillChange, PrefillSuggestion } from "../api/userTypes";
import { confirmedPatch, type GoalPick, tickedByDefault } from "../lib/flow";

type T = ReturnType<typeof useTranslations>;

function label(t: T, field: PrefillChange["field"], v: string): string {
  switch (field) {
    case "conditions":
      return t.has(`condition.${v}`) ? t(`condition.${v}`) : v;
    case "allergens":
      return isCanonicalAllergen(v) ? t(`allergen.${v}`) : v;
    case "custom_alerts":
      return t.has(`alert.${v}`) ? t(`alert.${v}`) : v;
    case "diet":
      return t.has(`diet.${v}`) ? t(`diet.${v}`) : v;
    case "goal":
      return t.has(`members.goal.${v}`) ? t(`members.goal.${v}`) : v;
  }
}

/** One line per change: lists show only what is added, diet/goal the new value. */
function line(t: T, c: PrefillChange): string {
  const key = `user_types.prefill.line.${c.field}`;
  if (c.field === "diet" || c.field === "goal") {
    const v = typeof c.value === "string" ? c.value : "";
    return t(key, { value: label(t, c.field, v) });
  }
  return t(key, {
    values: c.added.map((v) => label(t, c.field, v)).join(", "),
  });
}

/**
 * "Add these to your profile?" (decision 3, P9-R9). Every suggestion is a
 * checkbox, ticked only where the user's own follow-up asked for it; a goal
 * conflict is a radio list defaulting to neither. Only "Add to profile"
 * sends anything: ONE members PATCH with the confirmed values, behind the
 * existing health_data gate (a 403 opens the consent dialog, then retries).
 */
export function PrefillReview({
  prefill,
  note,
  onDone,
}: {
  prefill: PrefillSuggestion;
  /** Shown above the list (e.g. health tiles dropped after a declined consent). */
  note?: string;
  onDone: () => void;
}) {
  const t = useTranslations();
  const name = useId();
  const save = useSaveMember();
  const [ticked, setTicked] = useState<Set<number>>(
    () =>
      new Set(
        prefill.changes.flatMap((c, i) => (tickedByDefault(c) ? [i] : [])),
      ),
  );
  const [goal, setGoal] = useState<GoalPick>("neither");
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  async function apply() {
    setError(null);
    const body = confirmedPatch(prefill.changes, ticked, goal);
    if (!body) {
      onDone();
      return;
    }
    try {
      await save.mutateAsync({ id: prefill.member_id, body });
      onDone();
    } catch (e) {
      const err = e as ApiError;
      if (err.code === "consent_required") setAsking(true);
      else setError(err);
    }
  }

  const goals = prefill.goal_choice ?? [];
  return (
    <section className="space-y-4" data-testid="prefill-review">
      <SectionHeader
        as="h1"
        title={t("user_types.prefill.title")}
        description={t("user_types.prefill.body")}
      />
      {note ? (
        <p role="status" className="text-md font-medium text-text-primary">
          {note}
        </p>
      ) : null}
      <Card className="space-y-4">
        {prefill.changes.length === 0 && goals.length === 0 ? (
          <p className="text-md text-text-secondary">
            {t("user_types.prefill.nothing")}
          </p>
        ) : null}
        {prefill.changes.map((c, i) => (
          <label
            key={`${c.field}-${c.reason}`}
            className="flex min-h-11 items-start gap-3 text-md text-text-primary"
          >
            <input
              type="checkbox"
              className="mt-1 size-5 shrink-0"
              checked={ticked.has(i)}
              onChange={() =>
                setTicked((s) => {
                  const next = new Set(s);
                  if (next.has(i)) next.delete(i);
                  else next.add(i);
                  return next;
                })
              }
            />
            <span>{line(t, c)}</span>
          </label>
        ))}
        {goals.length > 0 ? (
          <fieldset className="space-y-2">
            <legend className={labelClass}>
              {t("user_types.prefill.goal_conflict")}
            </legend>
            {[...goals, "neither" as const].map((g) => (
              <label
                key={g}
                className="flex min-h-11 items-center gap-3 text-md"
              >
                <input
                  type="radio"
                  name={name}
                  className="size-5"
                  checked={goal === g}
                  onChange={() => setGoal(g)}
                />
                {g === "neither"
                  ? t("user_types.prefill.goal_neither")
                  : label(t, "goal", g)}
              </label>
            ))}
          </fieldset>
        ) : null}
      </Card>
      {error ? (
        <p role="alert" className="text-md text-text-primary">
          {t(errorKey(t, error))}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button onClick={apply} disabled={save.isPending}>
          {t("user_types.prefill.apply")}
        </Button>
        <Button variant="outline" onClick={onDone} disabled={save.isPending}>
          {t("user_types.prefill.not_now")}
        </Button>
      </div>
      {asking ? (
        <ConsentDialog
          onAgreed={() => {
            setAsking(false);
            void apply();
          }}
          onCancel={() => setAsking(false)}
        />
      ) : null}
    </section>
  );
}
