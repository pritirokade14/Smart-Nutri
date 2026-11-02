"use client";

import { hasLocale, useLocale, useTranslations } from "next-intl";
import { normalizeBarcode } from "@/features/scan/lib/barcode";
import { routing } from "@/i18n/routing";
import {
  type AnalyzeOut,
  analyzeErrorView,
  useAnalyzeBarcode,
} from "../api/useAnalyzeBarcode";
import { GradeChip } from "./GradeChip";
import { OffAttribution } from "./OffAttribution";
import { VerdictCard } from "./VerdictCard";

const HIGH_IN = new Set(["sugar", "fat", "sat_fat", "salt"]);

// The report is an untyped object in the contract; read only what we render.
function readReport(report: AnalyzeOut["report"]) {
  const ns = report.nutriscore as { grade?: unknown } | null | undefined;
  const grade = typeof ns?.grade === "string" ? ns.grade : null;
  const highIn = Array.isArray(report.high_in)
    ? (report.high_in as unknown[]).filter(
        (k): k is string => typeof k === "string" && HIGH_IN.has(k),
      )
    : [];
  return { grade, highIn };
}

function Analysis({ data, barcode }: { data: AnalyzeOut; barcode: string }) {
  const t = useTranslations();
  const { product } = data;
  const { grade, highIn } = readReport(data.report);
  return (
    <>
      <header className="space-y-(--spacing-1)">
        <h1 className="text-(length:--text-xl)">{product.name ?? barcode}</h1>
        {product.brand ? (
          <p className="text-(length:--text-md)">{product.brand}</p>
        ) : null}
      </header>

      <GradeChip grade={grade} />

      {highIn.length > 0 ? (
        <section className="space-y-(--spacing-2)">
          <h2 className="text-(length:--text-md)">
            {t("result.high_in_title")}
          </h2>
          <ul className="flex flex-wrap gap-(--spacing-2)">
            {highIn.map((k) => (
              <li
                key={k}
                className="rounded-(--radius-sm) border px-(--spacing-2) py-(--spacing-1) text-(length:--text-sm)"
              >
                {t(`high_in.${k}`)}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {/* One card per member, in the order the API sent them. */}
      <section className="space-y-(--spacing-3)">
        {data.verdicts.map((v) => (
          <VerdictCard key={v.member_id} verdict={v} />
        ))}
      </section>

      {product.attribution != null ? (
        <OffAttribution barcode={product.barcode ?? barcode} />
      ) : null}
    </>
  );
}

/** Logged-in result for one barcode: the API's verdicts, rendered as-is. */
export function ResultView({ barcode }: { barcode: string }) {
  const t = useTranslations();
  const locale = useLocale();
  const language = hasLocale(routing.locales, locale)
    ? locale
    : routing.defaultLocale;
  const code = normalizeBarcode(barcode);
  const query = useAnalyzeBarcode(barcode, language);

  let body: React.ReactNode;
  if (code === null) {
    body = (
      <p role="alert" className="text-(length:--text-md)">
        {t("error.invalid_barcode")}
      </p>
    );
  } else if (query.isPending) {
    body = (
      <p role="status" className="text-(length:--text-md)">
        {t("common.loading")}
      </p>
    );
  } else if (query.isError) {
    const view = analyzeErrorView(query.error);
    const message = t.has(view.messageKey)
      ? t(view.messageKey)
      : t("error.internal_error");
    body = (
      <section className="space-y-(--spacing-2)">
        <p role="alert" className="text-(length:--text-md)">
          {message}
        </p>
        {view.kind !== "invalid" ? (
          <button
            type="button"
            disabled={query.isFetching}
            onClick={() => query.refetch()}
            className="rounded-(--radius-md) border px-(--spacing-4) py-(--spacing-2) text-(length:--text-md)"
          >
            {t("scan.retry")}
          </button>
        ) : null}
      </section>
    );
  } else {
    body = <Analysis data={query.data} barcode={code} />;
  }

  return (
    <main className="mx-auto max-w-xl space-y-(--spacing-4) p-(--spacing-4)">
      {body}
      <footer className="space-y-(--spacing-2)">
        <p className="text-(length:--text-sm)">{t("common.disclaimer")}</p>
        <a
          href={`/${language}/scan`}
          className="inline-block rounded-(--radius-md) border px-(--spacing-4) py-(--spacing-2) text-(length:--text-md) underline"
        >
          {t("result.scan_another")}
        </a>
      </footer>
    </main>
  );
}
