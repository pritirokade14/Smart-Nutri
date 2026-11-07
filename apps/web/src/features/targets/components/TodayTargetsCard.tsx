"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button, buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { chipClass } from "@/components/ui/Chip";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import { formatAmount, shownTotal } from "@/features/history/lib/summary";
import { todayIst } from "@/features/meals/api/meals";
import { useSummary } from "@/features/meals/hooks/useMeals";
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

/** Consent withdrawn: the shown state is unknown, so the eye offers "hide". */
const UNKNOWN_DISPLAY = {
  numbers_hidden: { energy: false, macros: false },
} as TargetsOut;

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
 * One target row. Energy and protein show "{eaten} of {target}" with the
 * summary's eaten total; fat and carbs show the target only (eaten arrives
 * with the diary). No client-side comparison: the row renders what the API
 * returned, whatever the eaten total is.
 */
function TargetRow({
  label,
  target,
  eaten,
  unit,
  testId,
}: {
  label: string;
  target: number;
  eaten?: Eaten;
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
      ) : null}
    </li>
  );
}

function Ready({
  targets,
  primary,
}: {
  targets: TargetsOut;
  primary?: MemberOut;
}) {
  const t = useTranslations();
  const summary = useSummary(primary?.id, "day", todayIst());
  const s = summary.data;
  const eaten = (key: "energy_kcal" | "protein_g"): Eaten | undefined =>
    s
      ? {
          total: shownTotal(s.totals?.[key], s.incomplete?.[key] === true),
          incomplete: s.incomplete?.[key] === true,
        }
      : undefined;
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
            unit="targets.kcal_value"
          />
        ) : null}
        {!macros && targets.protein_g !== null ? (
          <TargetRow
            testId="target-protein"
            label={t("targets.protein")}
            target={targets.protein_g}
            eaten={eaten("protein_g")}
            unit="targets.g_value"
          />
        ) : null}
        {!macros && targets.fat_g !== null ? (
          <TargetRow
            testId="target-fat"
            label={t("targets.fat")}
            target={targets.fat_g}
            unit="targets.g_value"
          />
        ) : null}
        {!macros && targets.carbs_g !== null ? (
          <TargetRow
            testId="target-carbs"
            label={t("targets.carbs")}
            target={targets.carbs_g}
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
 * The Today "daily guide" card (Plan 10, slice 1): the API's targets as rows
 * (no rings: remaining and progress arrive with the diary), the eaten total
 * from the meal summary, and the eye toggle. A missing health_data consent is
 * an inline card with a grant button, never a redirect. Nothing is computed
 * here; hidden numbers arrive as null and stay hidden.
 */
export function TodayTargetsCard({ primary }: { primary?: MemberOut }) {
  const t = useTranslations();
  const locale = useLocale();
  const query = useTodayTargets();
  const [skipped, setSkipped] = useState(skippedThisSession);
  const [asking, setAsking] = useState(false);

  const title = t("home.cards.today_targets.title");
  const heading = (toggle?: TargetsOut) => (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h2
        id="home-card-today_targets-title"
        className="text-md font-semibold text-text-primary"
      >
        {title}
      </h2>
      {toggle ? <EyeToggle targets={toggle} /> : null}
    </div>
  );
  const shell = (children: React.ReactNode, toggle?: TargetsOut) => (
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
        UNKNOWN_DISPLAY,
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
        <Ready targets={targets} primary={primary} />
      )}
      <p className="text-sm text-text-secondary">{t("diary.disclaimer")}</p>
      <p className="text-sm text-text-secondary">
        {t("targets.pending_review")}
      </p>
    </>,
    targets,
  );
}
