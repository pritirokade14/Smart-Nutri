"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState } from "@/components/ui/Skeleton";
import { isGranted, type MemberOut } from "@/features/members/api/members";
import {
  ConsentDialog,
  errorKey,
} from "@/features/members/components/ConsentDialog";
import { useConsents, useMembers } from "@/features/members/hooks/useMembers";
import type { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/cn";
import type { GoalSettingsOut } from "../api/targets";
import { useGuideForm } from "../hooks/useGuideForm";
import { useGoalSettings } from "../hooks/useTargets";
import { type GuideStepId, problemMessage, problemStep } from "../lib/problems";
import { AboutYouStep } from "./AboutYouStep";
import { ActivityStep } from "./ActivityStep";
import { GoalStep } from "./GoalStep";
import { GuideResult } from "./GuideResult";
import { NumbersChoice } from "./NumbersChoice";

const STEPS: readonly GuideStepId[] = [
  "intro",
  "about",
  "activity",
  "goal",
  "guide",
];

function Flow({
  member,
  settings,
}: {
  member: MemberOut;
  settings: GoalSettingsOut | null;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const consents = useConsents();
  const [step, setStep] = useState<GuideStepId>("intro");
  const [asking, setAsking] = useState(false);
  const [underweightNote, setUnderweightNote] = useState(false);
  const form = useGuideForm({
    member,
    settings,
    previewing: step === "goal" || step === "guide",
  });
  const { values, set, preview, targets, saveGuide } = form;
  const error: ApiError | null = saveGuide.error ?? preview.error;

  // A guide error belongs to a field: land the user on it. An underweight
  // goal offers maintenance, preselected, with neutral copy.
  const code = error?.code;
  // biome-ignore lint/correctness/useExhaustiveDependencies: react to a new error only
  useEffect(() => {
    if (!error) return;
    const to = problemStep(error);
    if (to) setStep(to);
    if (error.code === "goal_not_allowed_underweight") {
      setUnderweightNote(true);
      set("direction", "maintain");
    }
  }, [error]);

  const home = () => router.push(`/${locale}/home`);

  async function doSave() {
    try {
      await form.save();
      home();
    } catch (e) {
      if ((e as ApiError).code === "consent_required") setAsking(true);
    }
  }

  function onSave() {
    // The API is the gate; asking first just saves a round trip.
    if (consents.isSuccess && !isGranted(consents.data, "health_data")) {
      setAsking(true);
      return;
    }
    void doSave();
  }

  const index = STEPS.indexOf(step);
  const next = STEPS[index + 1];
  const canSave =
    targets !== undefined &&
    (targets.status === "ready" || targets.status === "paused_pregnancy") &&
    (targets.unusual_fields.length === 0 || form.unusualConfirmed) &&
    !saveGuide.isPending;
  const missing =
    targets?.status === "needs_body_data" ? targets.missing_fields : [];
  const bodyFatError =
    code === "body_fat_out_of_range" && error ? problemMessage(t, error) : null;
  const targetWeightError =
    code === "target_weight_too_low" && error ? problemMessage(t, error) : null;
  const saveError =
    saveGuide.error &&
    code !== "consent_required" &&
    !problemStep(saveGuide.error)
      ? t(errorKey(t, saveGuide.error))
      : null;

  return (
    <div className="space-y-4" data-testid="guide-setup">
      <nav aria-label={t("targets.title")}>
        <ol className="flex flex-wrap gap-2">
          {STEPS.map((s, i) => (
            <li key={s}>
              <button
                type="button"
                data-testid={`step-nav-${s}`}
                aria-current={s === step ? "step" : undefined}
                className={cn(
                  "min-h-11 cursor-pointer rounded-full border px-4 text-sm font-medium",
                  s === step
                    ? "border-brand-primary bg-brand-soft text-brand-primary"
                    : "border-border-default bg-surface-default text-text-primary",
                )}
                onClick={() => setStep(s)}
              >
                {i + 1}.{" "}
                {t(s === "intro" ? "targets.intro.title" : `targets.step.${s}`)}
              </button>
            </li>
          ))}
        </ol>
      </nav>

      <Card className="space-y-4">
        {step === "intro" ? (
          <div className="space-y-4" data-testid="step-intro">
            <SectionHeader
              as="h1"
              title={t("targets.intro.title")}
              description={t("targets.intro.body")}
            />
            <NumbersChoice
              value={values.numbers_display}
              onChange={(v) => set("numbers_display", v)}
            />
            <Button variant="ghost" onClick={home}>
              {t("targets.skip")}
            </Button>
          </div>
        ) : null}
        {step === "about" ? (
          <AboutYouStep
            values={values}
            onChange={set}
            highlight={missing}
            bodyFatError={bodyFatError}
          />
        ) : null}
        {step === "activity" ? (
          <ActivityStep
            value={values.activity}
            onChange={(v) => set("activity", v)}
          />
        ) : null}
        {step === "goal" ? (
          <GoalStep
            values={values}
            onChange={set}
            rateOptions={targets?.rate_options ?? []}
            selectedRate={form.selectedRate}
            notice={underweightNote ? t("targets.underweight") : null}
            targetWeightError={targetWeightError}
          />
        ) : null}
        {step === "guide" ? (
          <GuideResult
            targets={targets}
            error={preview.error}
            loading={preview.isPending}
            onRetry={form.retryPreview}
            onEditBody={() => setStep("about")}
            unusualConfirmed={form.unusualConfirmed}
            onUnusualChange={form.setUnusualConfirmed}
          />
        ) : null}
        {saveError ? (
          <p role="alert" className="text-md text-text-primary">
            {saveError}
          </p>
        ) : null}
        <div className="flex flex-wrap gap-2">
          {next ? (
            <Button onClick={() => setStep(next)}>
              {t("user_types.continue")}
            </Button>
          ) : (
            <Button onClick={onSave} disabled={!canSave}>
              {t("targets.save")}
            </Button>
          )}
        </div>
      </Card>
      {asking ? (
        <ConsentDialog
          onAgreed={() => {
            setAsking(false);
            void doSave();
          }}
          onCancel={() => setAsking(false)}
        />
      ) : null}
    </div>
  );
}

/**
 * Daily guide setup (spec 7.1): intro and numbers choice, about you, activity,
 * goal, then the guide the API computed. One step at a time on every screen
 * size; the step buttons move freely between them. Nothing is saved until
 * "Save my daily guide".
 */
export function GuideSetup() {
  const t = useTranslations();
  const members = useMembers();
  const settings = useGoalSettings();
  const failed =
    members.error ??
    (settings.error?.code === "consent_required" ? null : settings.error);
  if (failed)
    return (
      <ErrorState
        message={t(errorKey(t, failed))}
        onRetry={() => {
          void members.refetch();
          void settings.refetch();
        }}
      />
    );
  const primary = members.data?.find((m) => m.is_primary) ?? members.data?.[0];
  if (!primary || (settings.isPending && !settings.isError))
    return <LoadingState label={t("common.loading")} />;
  return <Flow member={primary} settings={settings.data ?? null} />;
}
