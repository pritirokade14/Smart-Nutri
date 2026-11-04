"use client";

import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { inputClass, labelClass } from "@/components/ui/field";
import type { CompareSide } from "@/features/product/api/products";
import { parseAmount, pricePerScoop } from "../lib/pricePerScoop";

// Latin digits, 2 decimals (rupees and paise).
const MONEY = new Intl.NumberFormat("en", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * One product's price per scoop. The two numbers the user types live only
 * in this component's state: never in storage, the URL, a query key, a
 * request or an analytics event. Rebuilding the screen clears them.
 */
function Side({ s, side }: { s: "a" | "b"; side: CompareSide }) {
  const t = useTranslations();
  const id = useId();
  const [price, setPrice] = useState("");
  const [pack, setPack] = useState("");
  const value = pricePerScoop(
    parseAmount(price),
    parseAmount(pack),
    side.serving_size_g,
  );
  return (
    <div
      data-testid={`price-${s}`}
      className="space-y-3 rounded-md border border-border-default bg-surface-default p-3"
    >
      <p className="text-sm font-semibold break-words text-text-primary">
        {side.name}
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1">
          <label htmlFor={`${id}-price`} className={labelClass}>
            {t("protein.price_label")}
          </label>
          <input
            id={`${id}-price`}
            inputMode="decimal"
            autoComplete="off"
            className={inputClass}
            value={price}
            onChange={(e) => setPrice(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <label htmlFor={`${id}-pack`} className={labelClass}>
            {t("protein.pack_size_label")}
          </label>
          <input
            id={`${id}-pack`}
            inputMode="decimal"
            autoComplete="off"
            className={inputClass}
            value={pack}
            onChange={(e) => setPack(e.target.value)}
          />
        </div>
      </div>
      {value !== null ? (
        <p
          data-testid="price-result"
          className="flex flex-wrap gap-2 text-md text-text-primary"
        >
          <span>{t("protein.compare.price_scoop")}</span>
          <span className="font-semibold tabular-nums">
            {MONEY.format(value)}
          </span>
        </p>
      ) : null}
      <p className="text-sm text-text-secondary">{t("protein.price_note")}</p>
    </div>
  );
}

/** Price per scoop for both sides of a comparison (client-only arithmetic). */
export function PricePerScoop({ a, b }: { a: CompareSide; b: CompareSide }) {
  const t = useTranslations();
  return (
    <section
      aria-labelledby="price-per-scoop"
      className="space-y-2"
      data-testid="price-per-scoop"
    >
      <h3
        id="price-per-scoop"
        className="text-sm font-semibold text-text-secondary"
      >
        {t("protein.price_per_scoop")}
      </h3>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        <Side s="a" side={a} />
        <Side s="b" side={b} />
      </div>
    </section>
  );
}
