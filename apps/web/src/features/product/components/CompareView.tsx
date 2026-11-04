"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useId, useState } from "react";
import { pageClass } from "@/components/shell/page";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { ErrorState } from "@/components/ui/ErrorState";
import { inputClass, labelClass } from "@/components/ui/field";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState } from "@/components/ui/Skeleton";
import { useMembers } from "@/features/members/hooks/useMembers";
import { track } from "@/lib/analytics";
import { compareHref, compareParams, type ProductRef } from "../api/products";
import { useCompare } from "../hooks/useProducts";
import { CompareTable } from "./CompareTable";
import { SearchBox } from "./SearchBox";

const asSide = (r: ProductRef) =>
  "productId" in r
    ? { product_id: r.productId, barcode: null }
    : { product_id: null, barcode: r.barcode };

/**
 * /compare: two products side by side for one family member. With only the
 * first product, the user searches for the second.
 */
export function CompareView({ a, b }: { a: ProductRef; b: ProductRef | null }) {
  const t = useTranslations();
  const locale = useLocale();
  const selectId = useId();
  const members = useMembers();
  const [picked, setPicked] = useState<string | null>(null);
  const memberId = picked ?? members.data?.[0]?.id ?? null;
  // Wait for the members so the first request already carries the member.
  const compare = useCompare(a, members.isPending ? null : b, memberId);
  const loaded = compare.data !== undefined;

  useEffect(() => {
    if (loaded) track("compare_viewed");
  }, [loaded]);

  const aParams = compareParams("a", asSide(a)) ?? {};
  let body: React.ReactNode;
  if (!b) {
    body = (
      <SearchBox
        label={t("compare.pick_second")}
        hrefFor={(hit) => {
          const second = compareParams("b", hit);
          return second ? compareHref(locale, aParams, second) : null;
        }}
      />
    );
  } else if (compare.isError) {
    const key =
      compare.error.code === "off_unavailable"
        ? "scan.off_unavailable"
        : `error.${compare.error.code}`;
    body = (
      <ErrorState
        message={t.has(key) ? t(key) : t("error.internal_error")}
        onRetry={() => compare.refetch()}
        retrying={compare.isFetching}
      />
    );
  } else if (!compare.data) {
    body = <LoadingState label={t("common.loading")} />;
  } else {
    body = <CompareTable data={compare.data} />;
  }

  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("compare.title")} />
      {b && members.data && members.data.length > 1 ? (
        <div className="space-y-1">
          <label htmlFor={selectId} className={labelClass}>
            {t("history.member")}
          </label>
          <select
            id={selectId}
            value={memberId ?? ""}
            onChange={(e) => setPicked(e.target.value)}
            className={inputClass}
          >
            {members.data.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name.trim() !== ""
                  ? m.name
                  : m.is_primary
                    ? t("result.you")
                    : t(`share.relation.${m.relation}`)}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      {body}
      <DisclaimerFooter />
    </main>
  );
}
