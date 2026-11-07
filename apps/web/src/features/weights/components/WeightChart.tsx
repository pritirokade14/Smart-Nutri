"use client";

import { useLocale, useTranslations } from "next-intl";
import type { WeightTrendOut } from "../api/weights";
import { formatDate, formatWeight } from "../lib/format";

const W = 320;
const H = 160;
const PAD = 12;

/** Date order of the window decides x; the API's `y` (0 to 1) decides height. */
export function xOf(date: string, from: number, span: number): number {
  const ms = Date.parse(`${date}T00:00:00Z`);
  // Clamped to 0..1 like Android, so a date outside from..to stays in the chart.
  const f = span > 0 ? Math.min(1, Math.max(0, (ms - from) / span)) : 0.5;
  return PAD + f * (W - 2 * PAD);
}
const yOf = (y: number): number => PAD + (1 - y) * (H - 2 * PAD);

/**
 * The weight chart as inline SVG. Every position comes from the API: dates
 * give x, `y` gives height (the shape survives hidden numbers). Raw weigh-ins
 * are neutral dots (left-out ones hollow); the trend is a brand line. There
 * are no axis numbers; a table lists the dates, and kg when they are shown.
 */
export function WeightChart({ trend }: { trend: WeightTrendOut }) {
  const t = useTranslations();
  const locale = useLocale();
  const hidden = trend.numbers_hidden;
  // x spans the requested range from..to (as on Android), not the data.
  const from = Date.parse(`${trend.from}T00:00:00Z`);
  const span = Date.parse(`${trend.to}T00:00:00Z`) - from;
  const line = trend.trend
    .filter((p) => p.y != null)
    .map((p) => `${xOf(p.date, from, span)},${yOf(p.y as number)}`)
    .join(" ");
  const kgByDate = new Map(trend.trend.map((p) => [p.date, p.trend_kg]));
  return (
    <figure className="space-y-2" data-testid="weight-chart">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-labelledby="weight-chart-title"
        className="h-auto w-full text-text-secondary"
      >
        <title id="weight-chart-title">{t("weight.trend")}</title>
        <polyline
          data-testid="weight-trend-line"
          points={line}
          fill="none"
          strokeWidth={2.5}
          strokeLinejoin="round"
          strokeLinecap="round"
          className="stroke-brand-primary"
        />
        {trend.points
          .filter((p) => p.y != null)
          .map((p) => (
            <circle
              key={p.date}
              data-testid={p.outlier ? "weight-dot-outlier" : "weight-dot"}
              cx={xOf(p.date, from, span)}
              cy={yOf(p.y as number)}
              r={3.5}
              strokeWidth={1.5}
              className={
                p.outlier
                  ? "fill-transparent stroke-text-secondary"
                  : "fill-text-secondary stroke-text-secondary"
              }
            >
              {p.outlier ? <title>{t("weight.outlier")}</title> : null}
            </circle>
          ))}
      </svg>
      <table className="sr-only" data-testid="weight-chart-table">
        <caption>{t("weight.trend")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("weight.date")}</th>
            {hidden ? null : <th scope="col">{t("weight.title")}</th>}
            {hidden ? null : <th scope="col">{t("weight.trend")}</th>}
          </tr>
        </thead>
        <tbody>
          {trend.points.map((p) => (
            <tr key={p.date}>
              <td data-allow-digits>{formatDate(p.date, locale)}</td>
              {hidden ? null : (
                <td>
                  {p.weight_kg == null
                    ? ""
                    : t("weight.kg_value", {
                        value: formatWeight(p.weight_kg),
                      })}
                  {p.outlier ? ` (${t("weight.outlier")})` : ""}
                </td>
              )}
              {hidden ? null : (
                <td>
                  {kgByDate.get(p.date) == null
                    ? ""
                    : t("weight.kg_value", {
                        value: formatWeight(kgByDate.get(p.date) as number),
                      })}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
