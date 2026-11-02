import { useLocale, useTranslations } from "next-intl";
import type { PublicProductOut } from "../api/public-product";

const OFF_IMAGE_PREFIX = "https://images.openfoodfacts.org/";
const GRADE_CLASS: Record<string, string> = {
  A: "bg-(--color-grade-a)",
  B: "bg-(--color-grade-b)",
  C: "bg-(--color-grade-c)",
  D: "bg-(--color-grade-d)",
  E: "bg-(--color-grade-e)",
};
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
    <main className="mx-auto max-w-xl space-y-(--spacing-4) p-(--spacing-4)">
      <header className="space-y-(--spacing-2)">
        {image ? (
          // biome-ignore lint/performance/noImgElement: next/image injects inline styles, blocked by our CSP
          <img
            src={image}
            alt={name}
            width={192}
            height={192}
            className="h-48 w-48 rounded-(--radius-md) object-contain"
          />
        ) : null}
        <h1 className="text-(length:--text-xl)">{name}</h1>
        {product.brand ? (
          <p className="text-(length:--text-md)">{product.brand}</p>
        ) : null}
      </header>

      <section className="space-y-(--spacing-2)">
        {grade ? (
          <p
            className={`inline-block rounded-(--radius-md) px-(--spacing-3) py-(--spacing-1) text-(length:--text-lg) ${GRADE_CLASS[grade] ?? ""}`}
          >
            {t("result.grade", { grade })}
          </p>
        ) : (
          <p className="text-(length:--text-sm)">
            {t("nutriscore.insufficient_data")}
          </p>
        )}
        <p className="text-(length:--text-sm)">
          {t("nutriscore.calculated_by")}
        </p>
      </section>

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

      {shownClaims.length > 0 ? (
        <section className="space-y-(--spacing-2)">
          <ul className="space-y-(--spacing-2)">
            {shownClaims.map((c) => (
              <li key={c.claim} className="text-(length:--text-sm)">
                <p className="text-(length:--text-md)">
                  {t(`claim.${c.claim}`)}
                </p>
                <p>{t(`claim_verdict.${c.verdict}`)}</p>
                {t.has(`claim_reason.${c.reason_code}`) ? (
                  <p>{t(`claim_reason.${c.reason_code}`, c.params)}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="space-y-(--spacing-2)">
        <h2 className="text-(length:--text-md)">{t("result.ingredients")}</h2>
        <p className="text-(length:--text-sm)">
          {product.ingredients.length > 0
            ? product.ingredients.join(", ")
            : t("result.no_ingredients")}
        </p>
      </section>

      <a
        href={`/${locale}/sign-in?next=/${locale}/result/${barcode}`}
        className="inline-block rounded-(--radius-md) border px-(--spacing-4) py-(--spacing-2) text-(length:--text-md) underline"
      >
        {t("product.public_cta")}
      </a>

      <footer className="space-y-(--spacing-2) text-(length:--text-sm)">
        <p>{t("common.disclaimer")}</p>
        {product.attribution ? (
          <p>
            <a
              href={`https://world.openfoodfacts.org/product/${barcode}`}
              rel="noopener noreferrer"
              className="underline"
            >
              {t("attribution.off")}
            </a>
          </p>
        ) : null}
      </footer>
    </main>
  );
}
