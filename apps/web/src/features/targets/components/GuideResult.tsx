"use client";

import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import type { ApiError } from "@/lib/api/errors";
import type { TargetsOut } from "../api/targets";
import { formatInt } from "../lib/format";
import { problemMessage } from "../lib/problems";
import { anyHidden, fieldLabelKey, statusMessage } from "../lib/status";
import { FlagNotes } from "./FlagNotes";
import { TargetsExplanation } from "./TargetsExplanation";

/**
 * Step 5, "Your daily guide": the `targets_preview` result as the API sent it.
 * Numbers the user chose to hide are null and never shown. Always carries the
 * disclaimer, the pending-review note and the kidney note.
 */
export function GuideResult({
  targets,
  error,
  loading,
  onRetry,
  onEditBody,
  unusualConfirmed,
  onUnusualChange,
}: {
  targets: TargetsOut | undefined;
  error: ApiError | null;
  loading: boolean;
  onRetry: () => void;
  /** Back to the body-data step (for `needs_body_data`). */
  onEditBody: () => void;
  unusualConfirmed: boolean;
  onUnusualChange: (next: boolean) => void;
}) {
  const t = useTranslations();
  if (error)
    return (
      <ErrorState
        message={problemMessage(t, error)}
        onRetry={onRetry}
        retrying={loading}
      />
    );
  if (!targets) return <LoadingState label={t("common.loading")} />;

  const message = statusMessage(t, targets);
  const rows = [
    {
      key: "energy",
      hidden: targets.numbers_hidden.energy,
      value: targets.energy_kcal,
      format: (n: number) => t("targets.kcal_value", { value: formatInt(n) }),
    },
    {
      key: "protein",
      hidden: targets.numbers_hidden.macros,
      value: targets.protein_g,
      format: (n: number) => t("targets.g_value", { value: formatInt(n) }),
    },
    {
      key: "fat",
      hidden: targets.numbers_hidden.macros,
      value: targets.fat_g,
      format: (n: number) => t("targets.g_value", { value: formatInt(n) }),
    },
    {
      key: "carbs",
      hidden: targets.numbers_hidden.macros,
      value: targets.carbs_g,
      format: (n: number) => t("targets.g_value", { value: formatInt(n) }),
    },
  ] as const;
  const unusual = targets.unusual_fields;
  return (
    <div className="space-y-4" data-testid="step-guide">
      {message ? (
        <div className="space-y-2">
          <p role="status" className="text-md font-medium text-text-primary">
            {message}
          </p>
          {targets.status === "needs_body_data" ? (
            <Button variant="outline" onClick={onEditBody}>
              {t("targets.step.about")}
            </Button>
          ) : null}
        </div>
      ) : null}
      {targets.status === "ready" ? (
        <>
          <ul
            className="divide-y divide-border-default"
            data-testid="guide-rows"
          >
            {rows.map((r) =>
              r.hidden || r.value === null ? null : (
                <li
                  key={r.key}
                  data-row={r.key}
                  className="flex items-baseline justify-between gap-2 py-2"
                >
                  <span className="text-sm font-semibold text-text-secondary">
                    {t(`targets.${r.key}`)}
                  </span>
                  <span className="text-md font-semibold text-text-primary">
                    {r.format(r.value)}
                  </span>
                </li>
              ),
            )}
          </ul>
          {anyHidden(targets) ? (
            <p className="text-sm text-text-secondary">
              {t("diary.hidden_numbers")}
            </p>
          ) : null}
          <FlagNotes targets={targets} />
          <TargetsExplanation targets={targets} />
          {unusual.length > 0 ? (
            <label className="flex min-h-11 items-start gap-3 text-md text-text-primary">
              <input
                type="checkbox"
                className="mt-1 size-5 shrink-0"
                checked={unusualConfirmed}
                onChange={(e) => onUnusualChange(e.target.checked)}
              />
              <span>
                {t("targets.unusual_confirm", {
                  fields: unusual
                    .map((f) => {
                      const key = fieldLabelKey(f);
                      return key ? t(key) : f;
                    })
                    .join(", "),
                })}
              </span>
            </label>
          ) : null}
          <p className="text-sm text-text-secondary">
            {t("protein.kidney_note")}
          </p>
        </>
      ) : null}
      <p className="text-sm text-text-secondary">{t("diary.disclaimer")}</p>
      <p className="text-sm text-text-secondary">
        {t("targets.pending_review")}
      </p>
    </div>
  );
}
