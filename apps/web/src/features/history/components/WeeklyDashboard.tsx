import { useLocale, useTranslations } from "next-intl";
import { cardClass } from "@/components/ui/Card";
import { InfoIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";
import type { DaySummary, Summary } from "@/features/meals/api/meals";
import { cn } from "@/lib/cn";
import {
  type Band,
  dayLabel,
  formatAmount,
  NUTRIENTS,
  type NutrientKey,
  readBand,
  readFlag,
  readTotal,
  shownBand,
  shownTotal,
} from "../lib/summary";
import { BandBadge } from "./BandBadge";

// Bar heights in tenths, as literal classes (the CSP allows no inline styles
// and Tailwind only generates classes it can see).
const HEIGHT = [
  "h-[4%]",
  "h-[10%]",
  "h-[20%]",
  "h-[30%]",
  "h-[40%]",
  "h-[50%]",
  "h-[60%]",
  "h-[70%]",
  "h-[80%]",
  "h-[90%]",
  "h-full",
] as const;

/** Bar height relative to the week's largest shown day (presentation only). */
function heightClass(value: number, max: number): string {
  if (max <= 0 || value <= 0) return HEIGHT[0];
  return HEIGHT[Math.max(1, Math.round((value / max) * 10))];
}

type Nutrient = (typeof NUTRIENTS)[number];

function dayTotal(day: DaySummary, key: NutrientKey): number | null {
  // Nothing logged is "nothing logged", never a 0 total.
  if (day.items === 0) return null;
  return shownTotal(readTotal(day.totals, key), readFlag(day.incomplete, key));
}

function NutrientWeek({
  nutrient,
  summary,
}: {
  nutrient: Nutrient;
  summary: Summary;
}) {
  const t = useTranslations("summary");
  const locale = useLocale();
  const { key, banded } = nutrient;
  const total = shownTotal(
    readTotal(summary.totals, key),
    readFlag(summary.incomplete, key),
  );
  const weekBand = shownBand(readBand(summary.bands, nutrient.band), total);
  const incomplete =
    readFlag(summary.incomplete, key) ||
    summary.days.some((d) => readFlag(d.incomplete, key));
  const amount = (n: number) =>
    key === "energy_kcal"
      ? t("kcal_total", { total: formatAmount(n) })
      : t("total_g", { total: formatAmount(n) });
  const days = summary.days.map((day) => {
    const value = dayTotal(day, key);
    const band: Band | undefined = banded
      ? shownBand(readBand(day.bands, nutrient.band), value)
      : undefined;
    return { day, value, band };
  });
  const max = Math.max(0, ...days.map((d) => d.value ?? 0));

  return (
    <section
      data-testid={`nutrient-${key}`}
      aria-labelledby={`week-${key}`}
      className={cn(cardClass, "space-y-3 p-4 sm:p-5")}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <h3
            id={`week-${key}`}
            className="text-md font-semibold text-text-primary"
          >
            {t(`nutrient.${key}`)}
          </h3>
          <p
            data-testid="week-total"
            className="text-lg font-bold text-text-primary"
          >
            {total === null ? t("band.unknown") : amount(total)}
          </p>
        </div>
        {banded ? <BandBadge band={weekBand} /> : null}
      </div>

      <ol className="grid h-32 grid-cols-7 items-end gap-1 sm:gap-2">
        {days.map(({ day, value, band }) => {
          const label = dayLabel(day.date, locale);
          const text =
            day.items === 0
              ? t("nothing_logged")
              : value === null
                ? t("band.unknown")
                : amount(value);
          return (
            <li
              key={day.date}
              data-testid="day-bar"
              data-date={day.date}
              data-band={band}
              className="flex h-full flex-col items-center justify-end gap-1"
            >
              <div className="flex w-full flex-1 items-end justify-center">
                <div
                  data-testid="bar-fill"
                  aria-hidden="true"
                  className={cn(
                    "w-full max-w-8 rounded-t-sm",
                    value === null
                      ? "h-[4%] border border-dashed border-text-secondary"
                      : heightClass(value, max),
                    value !== null &&
                      (banded ? "bg-(--band-color)" : "bg-text-secondary/60"),
                  )}
                />
              </div>
              <span
                aria-hidden="true"
                className="text-center text-xs leading-tight text-text-secondary"
              >
                {label}
              </span>
              <span className="sr-only">
                <span className="block">{label}</span>
                <span className="block">{text}</span>
                {band && value !== null ? (
                  <span className="block">{t(`band.${band}`)}</span>
                ) : null}
              </span>
            </li>
          );
        })}
      </ol>

      {incomplete ? (
        <p className="text-sm text-text-secondary">{t("incomplete")}</p>
      ) : null}
      {key === "sugars_g" ? (
        <p className="text-sm text-text-secondary">{t("sugar_note")}</p>
      ) : null}
      {key === "energy_kcal" ? (
        <p className="text-sm text-text-secondary">{t("kcal_info")}</p>
      ) : null}
    </section>
  );
}

/**
 * The member's last 7 IST days, exactly as GET /v1/meals/summary?period=week
 * returned them: one bar per day for each nutrient, coloured by the API's
 * band (token variables via data-band; grey when unknown). Protein and
 * calories are neutral: protein is a target, not a limit, and there is no
 * calorie target. Week totals are plain totals, never set against a daily
 * limit.
 */
export function WeeklyDashboard({ summary }: { summary: Summary }) {
  const t = useTranslations("summary");
  return (
    <section
      data-testid="weekly-dashboard"
      aria-labelledby="weekly-title"
      className="space-y-3"
    >
      <SectionHeader id="weekly-title" title={t("title.week")} />
      {NUTRIENTS.map((n) => (
        <NutrientWeek key={n.key} nutrient={n} summary={summary} />
      ))}
      <aside className="space-y-1 rounded-md bg-surface-muted px-3 py-2 text-sm text-text-secondary">
        <p className="flex items-start gap-2">
          <InfoIcon className="mt-0.5 size-4 shrink-0" />
          <span>{t("week_note")}</span>
        </p>
        <p className="ps-6">{t("limits_note")}</p>
      </aside>
    </section>
  );
}
