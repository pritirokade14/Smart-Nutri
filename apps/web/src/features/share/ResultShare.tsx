"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { ShareButton } from "./ShareButton";
import {
  type ShareVerdict,
  shareMemberText,
  shareResultText,
  shareUrl,
} from "./shareText";

/**
 * Share a result. Every member is listed with exactly what would be shared
 * about them ("Ravi: Avoid"); the user unticks anyone to leave them out.
 * Needs the `verdict` namespace (the result page provides it).
 */
export function ResultShare({
  productName,
  grade,
  barcode,
  verdicts,
}: {
  productName: string;
  grade: string | null;
  barcode: string | null;
  verdicts: readonly ShareVerdict[];
}) {
  const t = useTranslations();
  const locale = useLocale();
  const [left, setLeft] = useState<ReadonlySet<number>>(new Set());
  const chosen = verdicts.filter((_, i) => !left.has(i));
  const url = shareUrl(locale, barcode);
  const text = shareResultText(
    t,
    { grade, verdicts: chosen },
    productName,
    url,
  );
  const toggle = (i: number) =>
    setLeft((s) => {
      const next = new Set(s);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  return (
    <ShareButton
      label={t("share.button")}
      text={text}
      url={url}
      event="share_result"
    >
      {verdicts.length > 0 ? (
        <fieldset className="space-y-1">
          <legend className="text-sm font-semibold text-text-secondary">
            {t("share.include")}
          </legend>
          {verdicts.map((v, i) => (
            <label
              // Response order is stable for one result.
              // biome-ignore lint/suspicious/noArrayIndexKey: no id is shared
              key={i}
              className="flex min-h-11 items-center gap-3 text-md text-text-primary"
            >
              <input
                type="checkbox"
                className="size-5"
                checked={!left.has(i)}
                onChange={() => toggle(i)}
              />
              <span>{shareMemberText(t, v)}</span>
            </label>
          ))}
        </fieldset>
      ) : null}
    </ShareButton>
  );
}
