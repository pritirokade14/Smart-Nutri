"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { InfoIcon } from "@/components/ui/icons";
import { LoadingState } from "@/components/ui/Skeleton";
import {
  ConsentDialog,
  errorKey,
} from "@/features/members/components/ConsentDialog";
import { useTodayTargets } from "@/features/targets/hooks/useTargets";
import { flagMessage } from "@/features/targets/lib/flagMessages";
import { cn } from "@/lib/cn";
import type { TrendDays, WeightTrendOut } from "../api/weights";
import { useWeightTrend } from "../hooks/useWeights";
import { formatDate, formatRate, formatWeight } from "../lib/format";
import { WeighInDialog } from "./WeighInDialog";
import { WeightChart } from "./WeightChart";
import { WeightList } from "./WeightList";

const RANGES = [30, 90, 365] as const;
// Today's targets flags that explain the weight story (shown as the API's own notes).
const TARGET_FLAGS = ["taper_active", "goal_weight_reached"] as const;

function ConsentCard({ onAgreed }: { onAgreed: () => void }) {
  const t = useTranslations();
  const [asking, setAsking] = useState(false);
  return (
    <Card className="space-y-3" data-testid="weight-consent">
      <p className="text-md text-text-primary">{t("weight.consent")}</p>
      <Button onClick={() => setAsking(true)}>{t("consent.agree")}</Button>
      {asking ? (
        <ConsentDialog
          onAgreed={() => {
            setAsking(false);
            onAgreed();
          }}
          onCancel={() => setAsking(false)}
        />
      ) : null}
    </Card>
  );
}

function Note({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <p
      data-testid={id}
      className="flex gap-2 rounded-md bg-surface-muted p-3 text-sm text-text-primary"
    >
      <InfoIcon className="mt-0.5 size-4 shrink-0" />
      <span>{children}</span>
    </p>
  );
}

/** Weekly rate, projection and flags exactly as the API sent them. */
function Insights({ trend }: { trend: WeightTrendOut }) {
  const t = useTranslations();
  const locale = useLocale();
  const targets = useTodayTargets();
  const shown = !trend.numbers_hidden;
  const rate = trend.weekly_rate;
  const proj = trend.projection;
  const taper = targets.data
    ? TARGET_FLAGS.filter((f) => targets.data.flags.includes(f))
        .map((f) => ({ f, text: flagMessage(t, f, targets.data) }))
        .filter(
          (n): n is { f: (typeof TARGET_FLAGS)[number]; text: string } =>
            n.text !== null,
        )
    : [];
  return (
    <div className="space-y-3" data-testid="weight-insights">
      {shown && rate ? (
        <p data-testid="weight-rate" className="text-md text-text-primary">
          {t("weight.weekly_rate", {
            kg: formatRate(rate.kg),
            pct: formatWeight(rate.pct_bw),
          })}
        </p>
      ) : null}
      {trend.projection_reason === "ready" ? (
        shown && proj?.target_kg != null && proj.date != null ? (
          <p
            data-testid="weight-projection"
            className="text-md text-text-primary"
          >
            {t("weight.projection", {
              target: formatWeight(proj.target_kg),
              date: formatDate(proj.date, locale),
            })}
          </p>
        ) : null
      ) : (
        <p
          data-testid="weight-no-projection"
          className="text-md text-text-secondary"
        >
          {t(`weight.no_projection.${trend.projection_reason}`)}
        </p>
      )}
      {trend.flags.includes("rapid_loss") ? (
        <Note id="weight-rapid-loss">
          {t("weight.rapid_loss", { pct: formatWeight(trend.rapid_loss_pct) })}
        </Note>
      ) : null}
      {taper.map((n) => (
        <Note key={n.f} id={`weight-flag-${n.f}`}>
          {n.text}
        </Note>
      ))}
    </div>
  );
}

/**
 * The Progress view: range chips, the weight chart, the weekly rate, the
 * projection (or why there is none), and the weigh-in list. Nothing is
 * computed here. Without health_data only the consent card shows.
 */
export function ProgressView({ today }: { today: string | undefined }) {
  const t = useTranslations();
  const [days, setDays] = useState<TrendDays>(90);
  const [adding, setAdding] = useState(false);
  const trend = useWeightTrend(days);

  if (trend.isError && trend.error.code === "consent_required") {
    return <ConsentCard onAgreed={() => void trend.refetch()} />;
  }
  return (
    <div className="space-y-4" data-testid="progress-view">
      <div className="flex flex-wrap items-center gap-2">
        <fieldset
          className="m-0 flex min-w-0 gap-2 border-0 p-0"
          data-testid="weight-range"
        >
          <legend className="sr-only">{t("weight.title")}</legend>
          {RANGES.map((r) => (
            <button
              key={r}
              type="button"
              aria-pressed={days === r}
              onClick={() => setDays(r)}
              className={cn(
                "min-h-9 cursor-pointer rounded-full px-4 text-sm font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
                days === r
                  ? "bg-brand-primary text-brand-on"
                  : "bg-surface-muted text-text-primary",
              )}
            >
              <span data-allow-digits>{t(`weight.range.${r}`)}</span>
            </button>
          ))}
        </fieldset>
        <Button
          data-testid="weight-add"
          disabled={today === undefined}
          onClick={() => setAdding(true)}
        >
          {t("weight.add")}
        </Button>
      </div>
      <Card className="space-y-4">
        {trend.isPending ? (
          <LoadingState label={t("common.loading")} />
        ) : trend.isError ? (
          <ErrorState
            message={t(errorKey(t, trend.error))}
            onRetry={() => void trend.refetch()}
            retrying={trend.isFetching}
          />
        ) : trend.data.points.length === 0 ? (
          <p
            data-testid="weight-empty-chart"
            className="text-md text-text-secondary"
          >
            {t("weight.empty")}
          </p>
        ) : (
          <>
            <WeightChart trend={trend.data} />
            <Insights trend={trend.data} />
          </>
        )}
        <p className="text-sm text-text-secondary">{t("diary.disclaimer")}</p>
      </Card>
      {today ? <WeightList today={today} /> : null}
      {adding && today ? (
        <WeighInDialog today={today} onClose={() => setAdding(false)} />
      ) : null}
    </div>
  );
}
