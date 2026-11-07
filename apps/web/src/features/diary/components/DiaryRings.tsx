"use client";

import { useTranslations } from "next-intl";
import { chipClass } from "@/components/ui/Chip";
import { formatAmount, shownTotal } from "@/features/history/lib/summary";
import { cn } from "@/lib/cn";
import type { DiaryDayOut, Macro4 } from "../api/diary";

export type SummaryView = "remaining" | "consumed";

const KEYS = ["energy_kcal", "protein_g", "carbs_g", "fat_g"] as const;
type Key = (typeof KEYS)[number];

const LABEL: Record<Key, string> = {
  energy_kcal: "targets.energy",
  protein_g: "targets.protein",
  carbs_g: "targets.carbs",
  fat_g: "targets.fat",
};

/** What one nutrient shows. Nothing here computes a value: it only picks. */
type Shown =
  | { kind: "hidden" }
  | { kind: "none" }
  | { kind: "incomplete"; lowerBound: number | null }
  | { kind: "left"; value: number }
  | { kind: "over"; value: number }
  | { kind: "eaten"; value: number };

function pick(day: DiaryDayOut, key: Key, view: SummaryView): Shown {
  const hidden =
    key === "energy_kcal"
      ? day.numbers_hidden.energy
      : day.numbers_hidden.macros;
  if (hidden) return { kind: "hidden" };
  const incomplete = day.incomplete[key] === true;
  // `remaining` is null as a whole unless the guide is ready: then the day
  // can only show what was eaten.
  if (view === "remaining" && day.remaining !== null) {
    const r = (day.remaining as Macro4)[key];
    if (incomplete || r === null)
      return { kind: "incomplete", lowerBound: null };
    return r < 0
      ? { kind: "over", value: Math.abs(r) }
      : { kind: "left", value: r };
  }
  const total = day.totals[key];
  if (incomplete)
    return { kind: "incomplete", lowerBound: shownTotal(total, true) };
  return total === null ? { kind: "none" } : { kind: "eaten", value: total };
}

/** A ring fill from the API's `progress` (0 to 1; over fills the ring). */
function fill(day: DiaryDayOut, key: Key): number {
  const p = day.progress?.[key];
  return typeof p === "number" ? Math.min(Math.max(p, 0), 1) : 0;
}

function Value({ shown, k }: { shown: Shown; k: Key }) {
  const t = useTranslations();
  const unit = (n: number) =>
    t(k === "energy_kcal" ? "targets.kcal_value" : "targets.g_value", {
      value: formatAmount(n),
    });
  switch (shown.kind) {
    case "hidden":
    case "none":
      return null;
    case "incomplete":
      return (
        <span className="inline-flex flex-wrap items-center gap-1.5">
          {shown.lowerBound !== null ? (
            <span data-testid={`value-${k}`}>{unit(shown.lowerBound)}</span>
          ) : null}
          <span className={chipClass} data-testid={`incomplete-${k}`}>
            {t("diary.incomplete")}
          </span>
        </span>
      );
    case "left":
      return (
        <span data-testid={`value-${k}`}>
          {t("diary.left", { value: unit(shown.value) })}
        </span>
      );
    case "over":
      return (
        <span data-testid={`value-${k}`} data-over="true">
          {t("diary.over", { value: unit(shown.value) })}
        </span>
      );
    case "eaten":
      return <span data-testid={`value-${k}`}>{unit(shown.value)}</span>;
  }
}

const R = 42;
const C = 2 * Math.PI * R;

function Ring({ fraction, over }: { fraction: number; over: boolean }) {
  return (
    <svg viewBox="0 0 100 100" className="size-28 shrink-0" aria-hidden="true">
      <circle
        cx="50"
        cy="50"
        r={R}
        fill="none"
        strokeWidth="10"
        className="stroke-surface-muted"
      />
      <circle
        cx="50"
        cy="50"
        r={R}
        fill="none"
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={`${C * fraction} ${C}`}
        transform="rotate(-90 50 50)"
        data-testid="ring-fill"
        className={over ? "stroke-text-secondary" : "stroke-brand-primary"}
      />
    </svg>
  );
}

function Bar({ fraction, over }: { fraction: number; over: boolean }) {
  return (
    <div
      aria-hidden="true"
      className="h-2 w-full overflow-hidden rounded-full bg-surface-muted"
    >
      <div
        data-testid="bar-fill"
        style={{ width: `${Math.round(fraction * 100)}%` }}
        className={cn(
          "h-full rounded-full",
          over ? "bg-text-secondary" : "bg-brand-primary",
        )}
      />
    </div>
  );
}

/**
 * The energy ring and the protein, carbs and fat bars. Values come from the
 * API's `remaining`, `progress` or totals (per `view`). An incomplete nutrient
 * is a grey chip, never a number and never 0. Over a target is the neutral
 * tone. Hidden numbers show the fill shape only, with no digit.
 */
export function DiaryRings({
  day,
  view,
}: {
  day: DiaryDayOut;
  view: SummaryView;
}) {
  const t = useTranslations();
  return (
    <div className="space-y-4" data-testid="diary-rings">
      {KEYS.map((k) => {
        const shown = pick(day, k, view);
        const over = shown.kind === "over";
        if (k === "energy_kcal") {
          return (
            <div
              key={k}
              data-testid={`ring-${k}`}
              className="flex items-center gap-4"
            >
              <Ring fraction={fill(day, k)} over={over} />
              <div className="min-w-0 space-y-1">
                <p className="text-sm font-semibold text-text-secondary">
                  {t(LABEL[k])}
                </p>
                <p className="text-lg font-semibold text-text-primary">
                  <Value shown={shown} k={k} />
                </p>
              </div>
            </div>
          );
        }
        return (
          <div key={k} data-testid={`ring-${k}`} className="space-y-1">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="text-sm font-semibold text-text-secondary">
                {t(LABEL[k])}
              </span>
              <span className="text-md font-semibold text-text-primary">
                <Value shown={shown} k={k} />
              </span>
            </div>
            <Bar fraction={fill(day, k)} over={over} />
          </div>
        );
      })}
    </div>
  );
}
