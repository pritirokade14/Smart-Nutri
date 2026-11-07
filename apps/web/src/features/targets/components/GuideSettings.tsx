"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button, buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/Dialog";
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
import type { GoalSettingsOut } from "../api/targets";
import { useGuideForm } from "../hooks/useGuideForm";
import {
  useGoalSettings,
  useResetGuide,
  useSetDisplay,
} from "../hooks/useTargets";
import { problemMessage } from "../lib/problems";
import { AboutYouStep } from "./AboutYouStep";
import { ActivityStep } from "./ActivityStep";
import { GoalStep } from "./GoalStep";
import { GuideResult } from "./GuideResult";
import { NumbersChoice } from "./NumbersChoice";

function Sections({
  member,
  settings,
  displayUnknown,
}: {
  member: MemberOut;
  settings: GoalSettingsOut | null;
  /** health_data withdrawn: the stored display value cannot be read. */
  displayUnknown: boolean;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const consents = useConsents();
  const form = useGuideForm({ member, settings, previewing: true });
  const setDisplay = useSetDisplay();
  const reset = useResetGuide();
  const [asking, setAsking] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const [saved, setSaved] = useState(false);
  const [picked, setPicked] = useState(false);
  const { values, set, preview, targets, saveGuide } = form;
  const error: ApiError | null = saveGuide.error ?? preview.error;

  async function doSave() {
    setSaved(false);
    try {
      await form.save();
      setSaved(true);
    } catch (e) {
      if ((e as ApiError).code === "consent_required") setAsking(true);
    }
  }
  function onSave() {
    if (consents.isSuccess && !isGranted(consents.data, "health_data")) {
      setAsking(true);
      return;
    }
    void doSave();
  }

  const canSave =
    form.answered &&
    targets !== undefined &&
    (targets.status === "ready" || targets.status === "paused_pregnancy") &&
    (targets.unusual_fields.length === 0 || form.unusualConfirmed) &&
    !saveGuide.isPending;
  const fieldError = (code: string) =>
    error?.code === code ? problemMessage(t, error) : null;
  const saveError =
    saveGuide.error && saveGuide.error.code !== "consent_required"
      ? problemMessage(t, saveGuide.error)
      : null;

  return (
    <div className="space-y-6" data-testid="guide-settings">
      <Card as="section" className="space-y-3">
        <SectionHeader title={t("targets.step.about")} />
        <AboutYouStep
          values={values}
          onChange={set}
          highlight={
            targets?.status === "needs_body_data" ? targets.missing_fields : []
          }
          bodyFatError={fieldError("body_fat_out_of_range")}
        />
      </Card>
      <Card as="section" className="space-y-3">
        <SectionHeader title={t("targets.step.activity")} />
        <ActivityStep
          value={values.activity}
          onChange={(v) => set("activity", v)}
        />
      </Card>
      <Card as="section" className="space-y-3">
        <SectionHeader title={t("targets.step.goal")} />
        <GoalStep
          values={values}
          onChange={set}
          rateOptions={targets?.rate_options ?? []}
          selectedRate={form.selectedRate}
          targetWeightError={fieldError("target_weight_too_low")}
          notice={fieldError("goal_not_allowed_underweight")}
        />
      </Card>
      <Card as="section" className="space-y-3">
        <NumbersChoice
          value={displayUnknown && !picked ? null : values.numbers_display}
          onChange={(v) => {
            setPicked(true);
            set("numbers_display", v);
            // The eye toggle's route: terms only, never revalidates the rest.
            // Always sent, even with no readable settings (health_data
            // withdrawn); a 404 (no settings yet) shows neutral copy below.
            setDisplay.mutate({ numbers_display: v });
          }}
        />
      </Card>
      <Card as="section" className="space-y-3">
        <SectionHeader title={t("targets.step.guide")} />
        <GuideResult
          targets={targets}
          error={preview.error}
          loading={preview.isPending}
          unanswered={!form.answered}
          onRetry={form.retryPreview}
          onEditBody={() => window.scrollTo({ top: 0 })}
          unusualConfirmed={form.unusualConfirmed}
          onUnusualChange={form.setUnusualConfirmed}
        />
        {setDisplay.error ? (
          <p role="alert" className="text-md text-text-primary">
            {setDisplay.error.status === 404
              ? t("targets.intro.body")
              : t(errorKey(t, setDisplay.error))}
          </p>
        ) : null}
        {reset.error ? (
          <p role="alert" className="text-md text-text-primary">
            {t(errorKey(t, reset.error))}
          </p>
        ) : null}
        {saveError ? (
          <p role="alert" className="text-md text-text-primary">
            {saveError}
          </p>
        ) : null}
        {saved ? (
          <p role="status" className="text-md font-medium text-text-primary">
            {t("members.saved")}
          </p>
        ) : null}
        <div className="flex flex-wrap gap-2">
          <Button onClick={onSave} disabled={!canSave}>
            {t("targets.save")}
          </Button>
          <Button
            variant="outline"
            onClick={() => setConfirmReset(true)}
            disabled={reset.isPending}
          >
            {t("settings.diary.reset")}
          </Button>
        </div>
      </Card>
      {confirmReset ? (
        <ConfirmDialog
          message={t("settings.diary.reset_confirm")}
          confirmLabel={t("settings.diary.reset")}
          cancelLabel={t("common.cancel")}
          busy={reset.isPending}
          onCancel={() => setConfirmReset(false)}
          onConfirm={() =>
            reset.mutate(undefined, {
              onSuccess: () => router.push(`/${locale}/profile`),
              onSettled: () => setConfirmReset(false),
            })
          }
        />
      ) : null}
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
 * "Diary and daily guide" in Profile (spec 7.9): the same sections as the
 * setup, editable on one page, the Numbers choice (saved at once through the
 * terms-only display route) and "Reset daily guide".
 */
export function GuideSettings() {
  const t = useTranslations();
  const locale = useLocale();
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
  return (
    <div className="space-y-4">
      <SectionHeader as="h1" title={t("settings.diary.title")} />
      <a
        href={`/${locale}/diary/meals`}
        className={buttonClass({ variant: "outline" })}
        data-testid="settings-meals-link"
      >
        {t("settings.diary.meals")}
      </a>
      <a
        href={`/${locale}/diary/my-foods`}
        className={buttonClass({ variant: "outline" })}
        data-testid="settings-my-foods-link"
      >
        {t("foods.my_foods")}
      </a>
      <Sections
        member={primary}
        settings={settings.data ?? null}
        displayUnknown={settings.error?.code === "consent_required"}
      />
    </div>
  );
}
