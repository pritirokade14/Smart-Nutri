"use client";

import { useTranslations } from "next-intl";
import { useEffect, useId, useState } from "react";
import { chipClass } from "@/components/ui/Chip";
import { ErrorState } from "@/components/ui/ErrorState";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { LoadingState } from "@/components/ui/Skeleton";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { FoodHit } from "../api/foods";
import { useFoodByBarcode, useFoodSearch } from "../hooks/useFoods";
import { SourceCredit } from "./SourceCredit";

const DEBOUNCE_MS = 300;
const GROUPS = ["mine", "indian", "packaged"] as const;
const BARCODE = /^\d{8,14}$/;

const KIND_KEY = {
  food: "foods.kind.food",
  product: "foods.kind.product",
  off: "foods.kind.product",
  custom_food: "foods.kind.custom_food",
  recipe: "foods.kind.recipe",
} as const;

/**
 * One search box over generic foods, Indian dishes and packaged products.
 * Debounced; results come grouped in the order the API sends them. A partial
 * answer shows its note, and "no results" only when nothing came back and
 * nothing failed.
 */
export function FoodSearch({ onPick }: { onPick: (hit: FoodHit) => void }) {
  const t = useTranslations();
  const id = useId();
  const [text, setText] = useState("");
  const [q, setQ] = useState("");
  useEffect(() => {
    const normal = text.trim().replace(/\s+/g, " ");
    const timer = setTimeout(() => setQ(normal), DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [text]);
  const search = useFoodSearch(q);
  // A typed barcode: look it up for logging (own food, product, or OFF).
  const code = BARCODE.test(q) ? q : null;
  const byCode = useFoodByBarcode(code);
  const items = search.data?.items ?? [];
  return (
    <div className="space-y-3" data-testid="food-search">
      <div className="space-y-1">
        <label htmlFor={id} className={labelClass}>
          {t("foods.search_placeholder")}
        </label>
        <input
          id={id}
          type="search"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={t("foods.search_placeholder")}
          className={inputClass}
        />
      </div>
      {code && byCode.data ? (
        <button
          type="button"
          data-testid="barcode-hit"
          onClick={() =>
            onPick({
              kind: byCode.data.kind,
              id: byCode.data.id,
              name: byCode.data.name,
              brand: byCode.data.brand,
              group: "packaged",
              is_dish: false,
              grade: null,
              attribution: byCode.data.attribution,
              attributions: byCode.data.attributions,
            })
          }
          className="flex min-h-11 w-full cursor-pointer flex-col gap-0.5 py-2 text-left hover:bg-surface-muted"
        >
          <span className="text-md font-medium break-words text-text-primary">
            {byCode.data.name}
          </span>
          <SourceCredit keys={byCode.data.attributions} />
        </button>
      ) : code && byCode.isError ? (
        <p role="alert" className={hintClass} data-testid="barcode-error">
          {t(errorKey(t, byCode.error))}
        </p>
      ) : null}
      {q.length >= 2 && search.isPending ? (
        <LoadingState label={t("common.loading")} lines={2} />
      ) : search.isError ? (
        <ErrorState
          message={t(errorKey(t, search.error))}
          onRetry={() => void search.refetch()}
          retrying={search.isFetching}
        />
      ) : search.data ? (
        <>
          {search.data.partial ? (
            <p role="status" className={hintClass} data-testid="food-partial">
              {t("foods.partial_results")}
            </p>
          ) : items.length === 0 ? (
            <p className={hintClass} data-testid="food-no-results">
              {t("foods.no_results")}
            </p>
          ) : null}
          {GROUPS.map((group) => {
            const hits = items.filter((h) => h.group === group);
            if (hits.length === 0) return null;
            return (
              <section
                key={group}
                data-testid={`food-group-${group}`}
                className="space-y-1"
              >
                <h3 className="text-sm font-semibold text-text-secondary">
                  {t(`foods.group.${group}`)}
                </h3>
                <ul className="divide-y divide-border-default">
                  {hits.map((h) => (
                    <li key={`${h.kind}:${h.id}`}>
                      <button
                        type="button"
                        data-testid="food-hit"
                        onClick={() => onPick(h)}
                        className="flex min-h-11 w-full cursor-pointer flex-col gap-0.5 py-2 text-left hover:bg-surface-muted"
                      >
                        <span className="flex flex-wrap items-center gap-2">
                          <span className="min-w-0 text-md font-medium break-words text-text-primary">
                            {h.name}
                          </span>
                          <span className={chipClass}>
                            {t(
                              h.is_dish ? "foods.kind.dish" : KIND_KEY[h.kind],
                            )}
                          </span>
                        </span>
                        {h.brand ? (
                          <span className="text-sm text-text-secondary">
                            {h.brand}
                          </span>
                        ) : null}
                        <SourceCredit keys={h.attributions} />
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            );
          })}
        </>
      ) : null}
    </div>
  );
}
