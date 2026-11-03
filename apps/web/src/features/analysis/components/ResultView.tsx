"use client";

import { useRouter } from "next/navigation";
import { hasLocale, useLocale, useTranslations } from "next-intl";
import { useEffect } from "react";
import { pageClass } from "@/components/shell/page";
import { buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { chipClass } from "@/components/ui/Chip";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { ErrorState } from "@/components/ui/ErrorState";
import { CameraIcon, ScanIcon } from "@/components/ui/icons";
import { LoadingState } from "@/components/ui/Skeleton";
import { LogMealButton } from "@/features/meals/components/LogMealButton";
import type { LogMealProduct } from "@/features/meals/components/LogMealDialog";
import type { ProductRef } from "@/features/product/api/products";
import { Alternatives } from "@/features/product/components/Alternatives";
import { normalizeBarcode } from "@/features/scan/lib/barcode";
import { ResultShare } from "@/features/share/ResultShare";
import { routing } from "@/i18n/routing";
import {
  type AnalyzeOut,
  analyzeErrorView,
  normalizeProductId,
  useAnalyze,
} from "../api/useAnalyzeBarcode";
import { readClaims } from "../lib/report";
import { ClaimsSection } from "./ClaimsSection";
import { ExplanationCard } from "./ExplanationCard";
import { GradeChip } from "./GradeChip";
import { NutritionTable } from "./NutritionTable";
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
  // Logging needs exactly one product reference: our id, else the barcode.
  const logProduct: LogMealProduct | null =
    product.product_id || offBarcode
      ? {
          productId: product.product_id,
          barcode: product.product_id ? null : offBarcode,
          name: product.name ?? offBarcode ?? "",
          servingSizeG: product.serving_size_g,
        }
      : null;
  const altRef: ProductRef | null = product.product_id
    ? { productId: product.product_id }
    : offBarcode
      ? { barcode: offBarcode }
      : null;
  const members = data.verdicts.map((v) => ({
    id: v.member_id,
    name: v.member_name,
    isPrimary: v.is_primary,
    relation: v.relation,
  }));
  return (
    <>
      <Card as="section" className="space-y-4">
        <header className="space-y-1">
          <h1 className="text-xl font-bold break-words text-text-primary sm:text-2xl">
            {product.name ?? product.barcode ?? barcode}
          </h1>
          {product.brand ? (
            <p className="text-md text-text-secondary">{product.brand}</p>
          ) : null}
        </header>

        <GradeChip grade={grade} />

        {highIn.length > 0 ? (
          <section className="space-y-2">
            <h2 className="text-sm font-semibold text-text-secondary">
              {t("result.high_in_title")}
            </h2>
            <ul className="flex flex-wrap gap-2">
              {highIn.map((k) => (
                <li key={k} className={chipClass}>
                  {t(`high_in.${k}`)}
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </Card>

      {/* One card per member, in the order the API sent them. */}
      <section aria-labelledby="members-title" className="space-y-3">
        {data.verdicts.length > 0 ? (
          <h2
            id="members-title"
            className="text-md font-semibold text-text-secondary"
          >
            {t("result.family_title")}
          </h2>
        ) : null}
        {data.verdicts.map((v) => (
          <div
            key={v.member_id}
            data-testid="member-result"
            className="space-y-2"
          >
            <VerdictCard verdict={v} />
            {logProduct ? (
              <LogMealButton
                product={logProduct}
                members={members}
                memberId={v.member_id}
              />
            ) : null}
          </div>
        ))}
      </section>

      <ResultShare
        productName={product.name ?? offBarcode ?? ""}
        grade={grade}
        barcode={offBarcode}
        verdicts={data.verdicts}
      />

      <ExplanationCard
        explanation={data.explanation}
        verdicts={data.verdicts}
      />

      <NutritionTable per100g={product.per_100g} />

      <ClaimsSection checks={readClaims(data.report)} />

      {altRef ? <Alternatives productRef={altRef} members={members} /> : null}

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
    body = <ErrorState message={t("error.invalid_barcode")} />;
  } else if (byId && id === null) {
    body = <ErrorState message={t("error.invalid_product_ref")} />;
  } else if (notFound && labelUrl) {
    body = (
      <a href={labelUrl} className={buttonClass({ size: "lg", block: true })}>
        <CameraIcon />
        {t("notfound.go_to_label")}
      </a>
    );
  } else if (query.isPending) {
    body = <LoadingState label={t("common.loading")} />;
  } else if (query.isError) {
    const view = analyzeErrorView(query.error);
    const message = t.has(view.messageKey)
      ? t(view.messageKey)
      : t("error.internal_error");
    body = (
      <ErrorState
        message={message}
        onRetry={view.kind !== "invalid" ? () => query.refetch() : undefined}
        retrying={query.isFetching}
        retryLabel={t("scan.retry")}
      />
    );
  } else {
    body = <Analysis data={query.data} barcode={code} />;
  }

  return (
    <main className={pageClass}>
      {body}
      <footer className="space-y-4">
        <DisclaimerFooter />
        <a
          href={`/${language}/scan`}
          className={buttonClass({ variant: "outline", block: true })}
        >
          <ScanIcon />
          {t("result.scan_another")}
        </a>
      </footer>
    </main>
  );
}
