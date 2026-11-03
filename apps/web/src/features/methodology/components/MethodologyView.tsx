import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { Card } from "@/components/ui/Card";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { InfoIcon } from "@/components/ui/icons";
import type { Methodology } from "../api/getMethodology";

type Section = Methodology["sections"][number];
type Source = Methodology["sources"][number];

// Values are shown exactly as the rules engine config sends them (keys are
// config identifiers, numbers in Latin digits); nothing is computed here.
function formatScalar(v: unknown): string {
  if (typeof v === "number") return String(v);
  if (typeof v === "boolean") return v ? "true" : "false";
  if (v === null || v === undefined) return "–";
  return String(v);
}

function isScalar(v: unknown): boolean {
  return v === null || ["string", "number", "boolean"].includes(typeof v);
}

function Value({ value }: { value: unknown }): ReactNode {
  if (isScalar(value))
    return <span className="font-mono">{formatScalar(value)}</span>;
  if (Array.isArray(value)) {
    if (value.every(isScalar))
      return (
        <span className="break-words">
          {value.map(formatScalar).join(", ")}
        </span>
      );
    return (
      <ul className="space-y-1">
        {value.map((item) => (
          <li key={JSON.stringify(item)}>
            <Value value={item} />
          </li>
        ))}
      </ul>
    );
  }
  const entries = Object.entries(value as Record<string, unknown>);
  if (entries.length === 0) return <span>–</span>;
  return (
    <dl className="grid grid-cols-[minmax(0,auto)_minmax(0,1fr)] gap-x-4 gap-y-1">
      {entries.map(([k, v]) => (
        <div key={k} className="contents">
          <dt>
            <code className="text-text-secondary">{k}</code>
          </dt>
          <dd className="min-w-0">
            <Value value={v} />
          </dd>
        </div>
      ))}
    </dl>
  );
}

function SourceRefs({
  ids,
  sources,
}: {
  ids: readonly string[];
  sources: ReadonlyMap<string, Source>;
}) {
  const t = useTranslations("methodology");
  const known = ids.filter((id) => sources.has(id));
  if (known.length === 0) return null;
  return (
    <p className="text-sm text-text-secondary">
      {t("based_on")}{" "}
      {known.map((id, i) => (
        <span key={id}>
          {i > 0 ? "; " : null}
          <a
            href={`#source-${id}`}
            className="underline underline-offset-4 hover:text-text-primary"
          >
            {sources.get(id)?.title}
          </a>
        </span>
      ))}
    </p>
  );
}

function SectionCard({
  section,
  sources,
}: {
  section: Section;
  sources: ReadonlyMap<string, Source>;
}) {
  const t = useTranslations("methodology");
  const key = `section.${section.id}`;
  const title = t.has(`${key}.title`) ? t(`${key}.title`) : section.id;
  const ids = [
    ...new Set([
      ...(section.threshold_sources ?? []),
      ...(section.rationale_sources ?? []),
    ]),
  ];
  // Long term lists (allergens, diet, alerts) start folded.
  const open = JSON.stringify(section.thresholds).length < 600;
  return (
    <Card
      as="section"
      data-testid={`methodology-${section.id}`}
      aria-labelledby={`m-${section.id}`}
      className="space-y-3"
    >
      <h2
        id={`m-${section.id}`}
        className="text-lg font-semibold text-text-primary"
      >
        {title}
      </h2>
      {t.has(`${key}.description`) ? (
        <p className="text-md text-text-primary">{t(`${key}.description`)}</p>
      ) : null}
      <details open={open} className="rounded-md bg-surface-muted p-3 text-sm">
        <summary className="cursor-pointer font-semibold text-text-primary">
          {t("values")}
        </summary>
        <div className="mt-2 text-text-primary">
          <Value value={section.thresholds} />
        </div>
      </details>
      <SourceRefs ids={ids} sources={sources} />
    </Card>
  );
}

/**
 * "How we score" (F12): every rule section from GET /v1/methodology with its
 * live values and sources. Public: generic rules only, no personal data.
 * Unverified source links are labelled and never followed for ranking.
 */
export function MethodologyView({ data }: { data: Methodology }) {
  const t = useTranslations();
  const sources = new Map(data.sources.map((s) => [s.id, s]));
  return (
    <>
      <header className="space-y-3">
        <h1 className="text-2xl font-bold text-text-primary sm:text-3xl">
          {t("methodology.title")}
        </h1>
        <p className="text-md text-text-primary">{t("methodology.intro")}</p>
        {data.pending_clinician_review ? (
          <p
            data-testid="pending-review"
            className="flex items-start gap-2 rounded-md border border-border-default bg-surface-muted px-3 py-2 text-md font-medium text-text-primary"
          >
            <InfoIcon className="mt-1 size-4 shrink-0" />
            <span>{t("methodology.pending_review")}</span>
          </p>
        ) : null}
        <DisclaimerFooter />
      </header>
      {data.sections.map((s) => (
        <SectionCard key={s.id} section={s} sources={sources} />
      ))}
      <section aria-labelledby="sources-title" className="space-y-3">
        <h2
          id="sources-title"
          className="text-lg font-semibold text-text-primary"
        >
          {t("methodology.sources_title")}
        </h2>
        <ul data-testid="sources" className="space-y-2 text-sm">
          {data.sources.map((s) => (
            <li
              key={s.id}
              id={`source-${s.id}`}
              data-testid={`source-${s.id}`}
              className="space-y-0.5"
            >
              <p className="font-medium text-text-primary">{s.title}</p>
              {s.url ? (
                <a
                  href={s.url}
                  rel="nofollow noopener noreferrer"
                  target="_blank"
                  className="break-all text-text-secondary underline underline-offset-4"
                >
                  {s.url}
                </a>
              ) : null}
              {s.url && !s.url_verified ? (
                <p className="text-text-secondary">
                  {t("methodology.url_unverified")}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      </section>
      <p className="text-sm text-text-secondary">
        {t("methodology.version", { version: data.version })}
      </p>
    </>
  );
}
