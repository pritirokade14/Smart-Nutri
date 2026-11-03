import { useLocale, useTranslations } from "next-intl";
import { pageClass } from "@/components/shell/page";
import { buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { chipClass } from "@/components/ui/Chip";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import {
  AlertTriangleIcon,
  CheckCircleIcon,
  FamilyIcon,
  QuestionCircleIcon,
} from "@/components/ui/icons";
import { NutriScoreChip } from "@/components/ui/NutriScoreChip";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { OffAttribution } from "@/features/analysis/components/OffAttribution";
import { PublicReportButton } from "@/features/reports/components/PublicReportButton";
import type { PublicProductOut } from "../api/public-product";

const OFF_IMAGE_PREFIX = "https://images.openfoodfacts.org/";
const HIGH_IN = new Set(["sugar", "fat", "sat_fat", "salt"]);
const CLAIM_VERDICTS = new Set(["supported", "contradicted", "unverifiable"]);

type ClaimCheck = {
  claim: string;
  verdict: string;
  reason_code: string;
  params: Record<string, string>;
};

// The report is an untyped object in the contract; read only what we render.
function readReport(report: PublicProductOut["report"]) {
  const ns = report.nutriscore as { grade?: unknown } | undefined;
  const grade = typeof ns?.grade === "string" ? ns.grade : null;
  const highIn = Array.isArray(report.high_in)
    ? (report.high_in as unknown[]).filter(
        (k): k is string => typeof k === "string" && HIGH_IN.has(k),
      )
    : [];
  const claims: ClaimCheck[] = [];
  if (Array.isArray(report.claims)) {
    for (const c of report.claims as Record<string, unknown>[]) {
      if (
        typeof c?.claim !== "string" ||
        typeof c.verdict !== "string" ||
        !CLAIM_VERDICTS.has(c.verdict) ||
        typeof c.reason_code !== "string"
      )
        continue;
      const params: Record<string, string> = {};
      for (const [k, v] of Object.entries(
        (c.params as Record<string, unknown>) ?? {},
      )) {
        params[k] = Array.isArray(v) ? v.join(", ") : String(v);
      }
      claims.push({
        claim: c.claim,
        verdict: c.verdict,
        reason_code: c.reason_code,
        params,
      });
    }
  }
  return { grade, highIn, claims };
}

// A claim check is about the pack's wording, not about any person: a neutral
// shape per outcome, never a member status colour.
const CLAIM_ICON = {
  supported: CheckCircleIcon,
  contradicted: AlertTriangleIcon,
  unverifiable: QuestionCircleIcon,
} as const;

/** Public product page: generic product information only, no member data. */
export function PublicProduct({
  data,
  barcode,
}: {
  data: PublicProductOut;
  barcode: string;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const { product } = data;
  const { grade, highIn, claims } = readReport(data.report);
  const name = product.name ?? barcode;
  const image = product.image_url?.startsWith(OFF_IMAGE_PREFIX)
    ? product.image_url
    : null;
  const shownClaims = claims.filter((c) => t.has(`claim.${c.claim}`));

  return (
    <main className={`${pageClass} max-w-3xl px-4 py-8 md:py-12`}>
      <Card as="section" className="space-y-5">
        <header className="flex flex-col gap-5 sm:flex-row sm:items-start">
          {image ? (
            <div className="flex size-48 shrink-0 items-center justify-center self-center rounded-lg bg-surface-muted p-3 sm:self-start">
              {/* biome-ignore lint/performance/noImgElement: next/image injects inline styles, blocked by our CSP */}
              <img
                src={image}
                alt={name}
                width={192}
                height={192}
                className="h-full w-full rounded-md object-contain"
              />
            </div>
          ) : null}
          <div className="min-w-0 space-y-4">
            <div className="space-y-1">
              <h1 className="text-xl font-bold break-words text-text-primary sm:text-2xl">
                {name}
              </h1>
              {product.brand ? (
                <p className="text-md text-text-secondary">{product.brand}</p>
              ) : null}
            </div>
            <NutriScoreChip grade={grade} showGradeLabel creditWithoutGrade />
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
          </div>
        </header>
      </Card>

      <section className="flex items-center gap-4 rounded-lg bg-brand-soft p-4 sm:p-5">
        <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-surface-default text-brand-primary">
          <FamilyIcon />
        </span>
        <a
          href={`/${locale}/sign-in?next=/${locale}/result/${barcode}`}
          className={buttonClass({ size: "lg" })}
        >
          {t("product.public_cta")}
        </a>
      </section>

      {shownClaims.length > 0 ? (
        <Card as="section" className="space-y-4">
          <SectionHeader title={t("product.claims_heading")} />
          <ul className="space-y-3">
            {shownClaims.map((c) => {
              const Icon =
                CLAIM_ICON[c.verdict as keyof typeof CLAIM_ICON] ??
                QuestionCircleIcon;
              return (
                <li
                  key={c.claim}
                  className="flex gap-3 rounded-md bg-surface-muted p-3 text-sm"
                >
                  <Icon className="mt-0.5 size-5 shrink-0 text-text-secondary" />
                  <div className="min-w-0 space-y-1">
                    <p className="text-md font-semibold text-text-primary">
                      {t("product.label_says", {
                        claim: t(`claim.${c.claim}`),
                      })}
                    </p>
                    <p className="font-medium text-text-primary">
                      {t(`claim_verdict.${c.verdict}`)}
                    </p>
                    {t.has(`claim_reason.${c.reason_code}`) ? (
                      <p className="text-text-secondary">
                        {t(`claim_reason.${c.reason_code}`, c.params)}
                      </p>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        </Card>
      ) : null}

      <Card as="section" className="space-y-3">
        <SectionHeader title={t("result.ingredients")} />
        <p className="text-md text-text-primary">
          {product.ingredients.length > 0
            ? product.ingredients.join(", ")
            : t("result.no_ingredients")}
        </p>
      </Card>

      <footer className="space-y-3">
        <DisclaimerFooter />
        {product.attribution ? <OffAttribution barcode={barcode} /> : null}
        {/* F14: only our own catalogue can be reported (needs product_id). */}
        {product.product_id ? (
          <PublicReportButton productId={product.product_id} />
        ) : null}
      </footer>
    </main>
  );
}
