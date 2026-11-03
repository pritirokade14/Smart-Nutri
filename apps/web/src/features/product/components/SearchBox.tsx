"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useId, useState } from "react";
import { cardClass } from "@/components/ui/Card";
import { chipClass } from "@/components/ui/Chip";
import { ErrorState } from "@/components/ui/ErrorState";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { ArrowRightIcon } from "@/components/ui/icons";
import { LoadingState } from "@/components/ui/Skeleton";
import { OffAttribution } from "@/features/analysis/components/OffAttribution";
import { cn } from "@/lib/cn";
import {
  productHref,
  SEARCH_MAX,
  SEARCH_MIN,
  type SearchHit,
} from "../api/products";
import { useSearch } from "../hooks/useProducts";

/**
 * Product search (ours first, then Open Food Facts). Each hit links to its
 * result page, or wherever `hrefFor` says (e.g. as the second product of a
 * comparison). Queries under 3 letters never reach the API; typing waits 600 ms,
 * and Enter searches at once.
 */
export function SearchBox({
  hrefFor,
  label,
  debounceMs = 600,
}: {
  hrefFor?: (hit: SearchHit) => string | null;
  /** Visible label; defaults to "Search products". */
  label?: string;
  debounceMs?: number;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const inputId = useId();
  const [raw, setRaw] = useState("");
  const [q, setQ] = useState("");
  useEffect(() => {
    const id = setTimeout(() => setQ(raw.trim()), debounceMs);
    return () => clearTimeout(id);
  }, [raw, debounceMs]);
  const search = useSearch(q);
  const link = hrefFor ?? ((h: SearchHit) => productHref(locale, h));

  let body: React.ReactNode = null;
  if (raw.trim() !== "" && raw.trim().length < SEARCH_MIN) {
    body = <p className={hintClass}>{t("search.too_short")}</p>;
  } else if (q.length >= SEARCH_MIN) {
    if (search.isPending) {
      body = <LoadingState label={t("common.loading")} lines={1} />;
    } else if (search.isError) {
      const key = `error.${search.error.code}`;
      body = (
        <ErrorState
          message={t.has(key) ? t(key) : t("error.internal_error")}
          onRetry={() => search.refetch()}
          retrying={search.isFetching}
        />
      );
    } else if (search.data.length === 0) {
      body = (
        <p className="text-md text-text-secondary">{t("search.no_results")}</p>
      );
    } else {
      body = (
        <>
          <ul className={cn(cardClass, "divide-y divide-border-default")}>
            {search.data.map((h) => {
              const href = link(h);
              const content = (
                <>
                  <span className="min-w-0 flex-1">
                    <span className="block text-md font-semibold break-words text-text-primary">
                      {h.name}
                    </span>
                    {h.brand ? (
                      <span className="block text-sm text-text-secondary">
                        {h.brand}
                      </span>
                    ) : null}
                  </span>
                  {h.grade ? (
                    <span className={chipClass}>
                      {t("result.grade", { grade: h.grade })}
                    </span>
                  ) : null}
                  <span className="text-sm text-text-secondary">
                    {t(`search.source.${h.source === "off" ? "off" : "ours"}`)}
                  </span>
                </>
              );
              return (
                <li
                  key={`${h.source}-${h.product_id ?? h.barcode ?? h.name}`}
                  data-testid="search-hit"
                >
                  {href ? (
                    <a
                      href={href}
                      className="flex min-h-11 flex-wrap items-center gap-3 px-4 py-3 hover:bg-surface-muted sm:px-5"
                    >
                      {content}
                      <ArrowRightIcon className="size-5 shrink-0 text-text-secondary" />
                    </a>
                  ) : (
                    <div className="flex flex-wrap items-center gap-3 px-4 py-3 sm:px-5">
                      {content}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
          {search.data.some((h) => h.off_degraded) ? (
            <p className={hintClass}>{t("search.off_degraded")}</p>
          ) : null}
          {search.data.some((h) => h.source === "off") ? (
            <OffAttribution barcode={null} />
          ) : null}
        </>
      );
    }
  }

  return (
    <div className="space-y-3">
      <div className="space-y-1">
        <label htmlFor={inputId} className={labelClass}>
          {label ?? t("search.title")}
        </label>
        <input
          id={inputId}
          type="search"
          autoComplete="off"
          maxLength={SEARCH_MAX}
          placeholder={t("search.placeholder")}
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              setQ(raw.trim());
            }
          }}
          className={inputClass}
        />
      </div>
      {body}
    </div>
  );
}
