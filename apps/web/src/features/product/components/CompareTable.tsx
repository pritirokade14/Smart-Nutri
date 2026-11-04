import { useTranslations } from "next-intl";
import { cardClass } from "@/components/ui/Card";
import { CheckCircleIcon } from "@/components/ui/icons";
import { NutriScoreChip } from "@/components/ui/NutriScoreChip";
import { VerdictBadge } from "@/components/ui/VerdictBadge";
import { OffAttribution } from "@/features/analysis/components/OffAttribution";
import { formatAmount } from "@/features/history/lib/summary";
import { PricePerScoop } from "@/features/protein/components/PricePerScoop";
import { cn } from "@/lib/cn";
import type { BetterSide, CompareOut, CompareSide } from "../api/products";

const ROWS = [
  "grade",
  "energy_kcal",
  "sugars_g",
  "salt_g",
  "sat_fat_g",
  "protein_g",
  "fiber_g",
  // Protein guide (decision 6b, part 5): per serving and per 100 kcal, as
  // the API computed them from report.protein (never derived here).
  "protein_per_serving_g",
  "protein_per_100kcal",
  "sugars_per_serving_g",
] as const;
type Row = (typeof ROWS)[number];

/** Rows read from the side itself (not per_100g), with their labels. */
const SIDE_ROWS: Partial<Record<Row, string>> = {
  protein_per_serving_g: "protein.compare.protein_serving",
  protein_per_100kcal: "protein.compare.protein_100kcal",
  sugars_per_serving_g: "protein.compare.sugar",
};

const rowLabel = (row: Row) => SIDE_ROWS[row] ?? `compare.row.${row}`;

const SIDES = new Set<string>(["a", "b", "same", "unknown"]);

/** The API's verdict on a row; anything unexpected marks no side. */
function betterOf(v: unknown): BetterSide {
  return typeof v === "string" && SIDES.has(v) ? (v as BetterSide) : "unknown";
}

// Two columns from the md breakpoint; one column (stacked) below it.
const COLUMNS = "grid grid-cols-1 gap-2 md:grid-cols-2";

function ProductHead({ side }: { side: CompareSide }) {
  return (
    <div className={cn(cardClass, "space-y-2 p-4")}>
      <div>
        <p className="text-md font-semibold break-words text-text-primary">
          {side.name}
        </p>
        {side.brand ? (
          <p className="text-sm text-text-secondary">{side.brand}</p>
        ) : null}
      </div>
      {side.member_status ? <VerdictBadge status={side.member_status} /> : null}
      {side.attribution != null ? (
        <OffAttribution barcode={side.barcode} />
      ) : null}
    </div>
  );
}

function Value({ row, side }: { row: Row; side: CompareSide }) {
  const t = useTranslations();
  if (row === "grade") {
    return <NutriScoreChip grade={side.grade} />;
  }
  const v = SIDE_ROWS[row]
    ? (side as unknown as Record<string, number | null | undefined>)[row]
    : (side.per_100g as Record<string, number | null | undefined>)[row];
  if (typeof v !== "number") {
    return (
      <span className="text-md text-text-secondary">
        {t("result.not_on_label")}
      </span>
    );
  }
  return (
    <span className="text-md font-semibold text-text-primary">
      {row === "energy_kcal"
        ? t("summary.kcal_total", { total: formatAmount(v) })
        : t("summary.total_g", { total: formatAmount(v) })}
    </span>
  );
}

/**
 * Two products side by side, exactly as GET /v1/products/compare returned
 * them. The better side of each row comes only from the API's `better`; the
 * browser never compares values. Two columns at md and up, stacked below.
 */
export function CompareTable({ data }: { data: CompareOut }) {
  const t = useTranslations();
  const sides = { a: data.a, b: data.b } as const;
  return (
    <section data-testid="compare-table" className="space-y-4">
      <div data-testid="compare-columns" className={COLUMNS}>
        <ProductHead side={data.a} />
        <ProductHead side={data.b} />
      </div>
      {ROWS.map((row) => {
        const better = betterOf((data.better as Record<string, unknown>)[row]);
        return (
          <section
            key={row}
            data-testid={`row-${row}`}
            aria-labelledby={`compare-${row}`}
            className="space-y-2"
          >
            <h3
              id={`compare-${row}`}
              className="text-sm font-semibold text-text-secondary"
            >
              {t(rowLabel(row))}
            </h3>
            <div data-testid="compare-columns" className={COLUMNS}>
              {(["a", "b"] as const).map((s) => {
                const isBetter = better === s;
                return (
                  <div
                    key={s}
                    data-testid={`cell-${s}`}
                    data-better={isBetter ? "true" : "false"}
                    className={cn(
                      "flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2",
                      isBetter
                        ? "border-2 border-brand-primary bg-brand-soft"
                        : "border-border-default bg-surface-default",
                    )}
                  >
                    <div className="min-w-0">
                      {/* Stacked: say which product each value belongs to. */}
                      <p className="text-sm break-words text-text-secondary md:sr-only">
                        {sides[s].name}
                      </p>
                      <Value row={row} side={sides[s]} />
                    </div>
                    {isBetter ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-surface-default px-2 py-0.5 text-sm font-semibold text-brand-primary">
                        <CheckCircleIcon className="size-4" />
                        {t("compare.better_chip")}
                      </span>
                    ) : null}
                  </div>
                );
              })}
            </div>
            <p className="text-sm text-text-secondary">
              {t(`compare.better.${better}`)}
            </p>
          </section>
        );
      })}
      <PricePerScoop a={data.a} b={data.b} />
    </section>
  );
}
