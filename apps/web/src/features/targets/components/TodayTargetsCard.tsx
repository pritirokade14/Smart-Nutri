"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button, buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { chipClass } from "@/components/ui/Chip";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import { useDiaryDay } from "@/features/diary/hooks/useDiaryDay";
import { formatAmount, shownTotal } from "@/features/history/lib/summary";
import type { MemberOut } from "@/features/members/api/members";
import {
  ConsentDialog,
  errorKey,
} from "@/features/members/components/ConsentDialog";
import type { TargetsOut } from "../api/targets";
import { useTodayTargets } from "../hooks/useTargets";
import { formatInt } from "../lib/format";
import { anyHidden, statusMessage } from "../lib/status";
import { EyeToggle } from "./EyeToggle";

/**
 * Consent withdrawn: the stored display value cannot be read, so the eye
 * starts at "hide" and then tracks the last value it sent (Android parity).
 */
function ConsentEye() {
  const [hidden, setHidden] = useState(false);
  return (
    <EyeToggle
      targets={{ numbers_hidden: { energy: hidden, macros: hidden } }}
      onSent={(next) => setHidden(next === "hide_all")}
    />
  );
}

const SKIP_KEY = "smartnutri.targets.skip";

function skippedThisSession(): boolean {
  try {
    return window.sessionStorage.getItem(SKIP_KEY) === "1";
  } catch {
    return false;
  }
}

type Eaten = { total: number | null; incomplete: boolean };

/**
 * One target row: "{eaten} of {target}" from the diary day's totals, and the
 * day's `remaining` ("X left", or "X over" with the absolute value, neutral
 * tone) when the API sent one. No client-side comparison or subtraction: the
 * row renders what the API returned, whatever the eaten total is.
 */
function TargetRow({
  label,
  target,
  eaten,
  remaining,
  unit,
  testId,
}: {
  label: string;
  target: number;
  eaten?: Eaten;
  remaining?: number | null;
  unit: "targets.kcal_value" | "targets.g_value";
  testId: string;
}) {
  const t = useTranslations();
  const fmt = (n: number) => t(unit, { value: formatInt(n) });
  const known = eaten && eaten.total !== null ? eaten.total : null;
  return (
    <li data-testid={testId} className="space-y-1 py-2">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-semibold text-text-secondary">
          {label}
        </span>
        <span className="text-md font-semibold text-text-primary">
          {known !== null
            ? t("diary.of_target", {
                eaten: t(unit, { value: formatAmount(known) }),
                target: fmt(target),
              })
            : fmt(target)}
        </span>
      </div>
      {eaten?.incomplete ? (
        <span className={chipClass} data-testid={`${testId}-incomplete`}>
          {t("diary.incomplete")}
        </span>
      ) : typeof remaining === "number" ? (
        <p
          data-testid={`${testId}-remaining`}
          className="text-sm text-text-secondary"
        >
          {t(remaining < 0 ? "diary.over" : "diary.left", {
            value: t(unit, { value: formatAmount(Math.abs(remaining)) }),
          })}
        </p>
      ) : null}
    </li>
  );
}

function Ready({ targets }: { targets: TargetsOut }) {
  const t = useTranslations();
  const day = useDiaryDay();
  const d = day.data;
  type Key = "energy_kcal" | "protein_g" | "fat_g" | "carbs_g";
  const eaten = (key: Key): Eaten | undefined =>
    d
      ? {
          total: shownTotal(d.totals[key], d.incomplete[key] === true),
          incomplete: d.incomplete[key] === true,
        }
      : undefined;
  // `remaining` is null as a whole unless the day's guide is ready.
  const left = (key: Key) => d?.remaining?.[key];
  const { energy, macros } = targets.numbers_hidden;
  return (
    <>
      <ul className="divide-y divide-border-default">
        {!energy && targets.energy_kcal !== null ? (
          <TargetRow
            testId="target-energy"
            label={t("targets.energy")}
            target={targets.energy_kcal}
            eaten={eaten("energy_kcal")}
            remaining={left("energy_kcal")}
            unit="targets.kcal_value"
          />
        ) : null}
        {!macros && targets.protein_g !== null ? (
          <TargetRow
            testId="target-protein"
            label={t("targets.protein")}
            target={targets.protein_g}
            eaten={eaten("protein_g")}
            remaining={left("protein_g")}
            unit="targets.g_value"
          />
        ) : null}
        {!macros && targets.fat_g !== null ? (
          <TargetRow
            testId="target-fat"
            label={t("targets.fat")}
            target={targets.fat_g}
            eaten={eaten("fat_g")}
            remaining={left("fat_g")}
            unit="targets.g_value"
          />
        ) : null}
        {!macros && targets.carbs_g !== null ? (
          <TargetRow
            testId="target-carbs"
            label={t("targets.carbs")}
            target={targets.carbs_g}
            eaten={eaten("carbs_g")}
            remaining={left("carbs_g")}
            unit="targets.g_value"
          />
        ) : null}
      </ul>
      {anyHidden(targets) ? (
        <p
          data-testid="numbers-hidden-note"
          className="text-sm text-text-secondary"
        >
          {t("diary.hidden_numbers")}
        </p>
      ) : null}
    </>
  );
}

/**
 * The Today "daily guide" card: the API's targets as rows, the eaten totals
 * and remaining from the diary day (GET /v1/diary/day), and the eye toggle. A missing health_data consent is
 * an inline card with a grant button, never a redirect. Nothing is computed
 * here; hidden numbers arrive as null and stay hidden.
 */
export function TodayTargetsCard(_props: { primary?: MemberOut } = {}) {
  const t = useTranslations();
  const locale = useLocale();
  const query = useTodayTargets();
  const [skipped, setSkipped] = useState(skippedThisSession);
  const [asking, setAsking] = useState(false);

  const title = t("home.cards.today_targets.title");
  const heading = (toggle?: React.ReactNode) => (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h2
        id="home-card-today_targets-title"
        className="text-md font-semibold text-text-primary"
      >
        {title}
      </h2>
      {toggle ?? null}
    </div>
  );
  const shell = (children: React.ReactNode, toggle?: React.ReactNode) => (
    <Card
      as="section"
      data-testid="home-card-today_targets"
      aria-labelledby="home-card-today_targets-title"
      className="space-y-3"
    >
      {heading(toggle)}
      {children}
    </Card>
  );

  if (query.isError) {
    if (query.error.code === "consent_required")
      return shell(
        <div className="space-y-3" data-testid="targets-consent">
          <p className="text-md text-text-primary">
            {t("diary.targets_consent")}
          </p>
          <Button onClick={() => setAsking(true)}>{t("consent.agree")}</Button>
          {asking ? (
            <ConsentDialog
              onAgreed={() => {
                setAsking(false);
                void query.refetch();
              }}
              onCancel={() => setAsking(false)}
            />
          ) : null}
        </div>,
        // The eye stays: the terms-only display route needs no health_data.
        <ConsentEye />,
      );
    return shell(
      <ErrorState
        message={t(errorKey(t, query.error))}
        onRetry={() => void query.refetch()}
        retrying={query.isFetching}
        className="border-none p-0 shadow-none sm:p-0"
      />,
    );
  }
  if (query.isPending || query.data === undefined)
    return shell(<LoadingState label={t("common.loading")} />);

  const targets = query.data;
  if (targets.status === "none") {
    if (skipped) return null;
    return shell(
      <div className="space-y-3" data-testid="targets-empty">
        <div className="flex flex-wrap gap-2">
          <a
            href={`/${locale}/guide/setup`}
            className={buttonClass({ variant: "primary" })}
          >
            {t("targets.setup_cta")}
          </a>
          <Button
            variant="ghost"
            onClick={() => {
              try {
                window.sessionStorage.setItem(SKIP_KEY, "1");
              } catch {
                // Private mode: dismissed for this view only.
              }
              setSkipped(true);
            }}
          >
            {t("targets.skip")}
          </Button>
        </div>
        <p className="text-sm text-text-secondary">{t("diary.disclaimer")}</p>
      </div>,
    );
  }

  const message = statusMessage(t, targets);
  return shell(
    <>
      {message ? (
        <div className="space-y-2">
          <p className="text-md text-text-primary">{message}</p>
          {targets.status === "needs_body_data" ? (
            <a
              href={`/${locale}/profile/guide`}
              className="inline-flex min-h-11 items-center text-md font-semibold text-brand-primary underline-offset-4 hover:underline"
            >
              {t("settings.diary.title")}
            </a>
          ) : null}
        </div>
      ) : (
        <Ready targets={targets} />
      )}
      <p className="text-sm text-text-secondary">{t("diary.disclaimer")}</p>
      <p className="text-sm text-text-secondary">
        {t("targets.pending_review")}
      </p>
    </>,
    <EyeToggle targets={targets} />,
  );
}
