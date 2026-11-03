"use client";

import { useRouter } from "next/navigation";
import { hasLocale, useLocale, useTranslations } from "next-intl";
import { useEffect } from "react";
import { normalizeBarcode } from "@/features/scan/lib/barcode";
import { routing } from "@/i18n/routing";
import {
  type AnalyzeOut,
  analyzeErrorView,
  normalizeProductId,
  useAnalyze,
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

function Analysis({
  data,
  barcode,
}: {
  data: AnalyzeOut;
  barcode: string | null;
}) {
  const t = useTranslations();
  const { product } = data;
  const { grade, highIn } = readReport(data.report);
  const offBarcode = product.barcode ?? barcode;
  return (
    <>
      <header className="space-y-(--spacing-1)">
        <h1 className="text-(length:--text-xl)">
          {product.name ?? product.barcode ?? barcode}
        </h1>
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

      {product.attribution != null && offBarcode ? (
        <OffAttribution barcode={offBarcode} />
      ) : null}
    </>
  );
}

type ResultRef =
  | { barcode: string; productId?: undefined }
  | { productId: string; barcode?: undefined };

/**
 * Logged-in result for one barcode, or for a saved product (by id): the API's
 * verdicts, rendered as-is. An unknown barcode (404) goes to the label flow.
 */
export function ResultView(props: ResultRef) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const language = hasLocale(routing.locales, locale)
    ? locale
    : routing.defaultLocale;
  const byId = props.productId !== undefined;
  const code = byId ? null : normalizeBarcode(props.barcode ?? "");
  const id = byId ? normalizeProductId(props.productId ?? "") : null;
  const query = useAnalyze(
    byId
      ? { productId: props.productId ?? "" }
      : { barcode: props.barcode ?? "" },
    language,
  );
  const notFound =
    !byId &&
    query.isError &&
    analyzeErrorView(query.error).kind === "not_found";
  const labelUrl = code
    ? `/${language}/scan/label?barcode=${encodeURIComponent(code)}`
    : null;

  // F15: an unknown barcode goes straight to label capture, carrying the code.
  useEffect(() => {
    if (notFound && labelUrl) router.replace(labelUrl);
  }, [notFound, labelUrl, router]);

  let body: React.ReactNode;
  if (!byId && code === null) {
    body = (
      <p role="alert" className="text-(length:--text-md)">
        {t("error.invalid_barcode")}
      </p>
    );
  } else if (byId && id === null) {
    body = (
      <p role="alert" className="text-(length:--text-md)">
        {t("error.invalid_product_ref")}
      </p>
    );
  } else if (notFound && labelUrl) {
    body = (
      <a
        href={labelUrl}
        className="inline-block rounded-(--radius-md) border px-(--spacing-4) py-(--spacing-2) text-(length:--text-md) underline"
      >
        {t("notfound.go_to_label")}
      </a>
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
