import { useTranslations } from "next-intl";
import { cardClass } from "@/components/ui/Card";
import type { Summary } from "@/features/meals/api/meals";
import { cn } from "@/lib/cn";
import {
  formatAmount,
  NUTRIENTS,
  readBand,
  readFlag,
  readTotal,
  shownBand,
  shownTotal,
} from "../lib/summary";
import { BandBadge } from "./BandBadge";

type Nutrient = (typeof NUTRIENTS)[number];

function limitOf(summary: Summary, n: Nutrient): number | null {
  const l = summary.limits;
  if (n.key === "sugars_g") return l.sugar_g ?? null;
  if (n.key === "salt_g") return l.salt_g ?? null;
  if (n.key === "protein_g") return l.protein_target_g ?? null;
  return null;
}

/**
 * One IST day's totals (GET /v1/meals/summary?period=day) against the
 * member's daily limits, as the API sent them. Sugar and salt carry the API
 * band; protein is progress towards a target (no band: it is never "within
 * limit"); calories are information only. A total the API could not compute
 * reads "Not enough data", never 0.
 */
export function DayTotals({ summary }: { summary: Summary }) {
  const t = useTranslations("summary");
  const day = summary.days[0];
  if (day && day.items === 0) {
    return (
      <p
        data-testid="day-totals-empty"
        className={cn(cardClass, "p-4 text-md text-text-secondary")}
      >
        {t("nothing_logged")}
      </p>
    );
  }
  return (
    <ul
      data-testid="day-totals"
      className={cn(cardClass, "divide-y divide-border-default")}
    >
      {NUTRIENTS.map((n) => {
        const incomplete = readFlag(summary.incomplete, n.key);
        const total = shownTotal(readTotal(summary.totals, n.key), incomplete);
        const limit = limitOf(summary, n);
        const value = (() => {
          if (total === null) return t("band.unknown");
          const v = formatAmount(total);
          if (n.key === "energy_kcal") return t("kcal_total", { total: v });
          if (limit === null) return t("total_g", { total: v });
          return n.key === "protein_g"
            ? t("protein_of_target", { total: v, target: formatAmount(limit) })
            : t("total_of_limit", { total: v, limit: formatAmount(limit) });
        })();
        return (
          <li
            key={n.key}
            data-testid={`day-${n.key}`}
            className="space-y-1 px-4 py-3 sm:px-5"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-text-secondary">
                  {t(`nutrient.${n.key}`)}
                </p>
                <p
                  data-testid="day-value"
                  className="text-md font-semibold text-text-primary"
                >
                  {value}
                </p>
              </div>
              {n.banded ? (
                <BandBadge
                  band={shownBand(readBand(summary.bands, n.band), total)}
                />
              ) : total === null ? (
                // Android parity: an unknown protein or kcal total gets the
                // grey "Not enough data" chip too.
                <BandBadge band="unknown" />
              ) : null}
            </div>
            {incomplete ? (
              <p className="text-sm text-text-secondary">{t("incomplete")}</p>
            ) : null}
            {n.key === "protein_g" && limit === null ? (
              <p className="text-sm text-text-secondary">
                {t("no_protein_target")}
              </p>
            ) : null}
            {n.key === "energy_kcal" ? (
              <p className="text-sm text-text-secondary">{t("kcal_info")}</p>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
