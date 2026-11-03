"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { buttonClass } from "@/components/ui/Button";
import { inputClass, labelClass } from "@/components/ui/field";
import { normalizeBarcode } from "../lib/barcode";

export function ManualBarcodeForm({
  onSubmit,
}: {
  onSubmit: (code: string) => void;
}) {
  const t = useTranslations("scan");
  const [value, setValue] = useState("");
  const [invalid, setInvalid] = useState(false);

  return (
    <form
      className="flex flex-col gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        const code = normalizeBarcode(value);
        setInvalid(code === null);
        if (code) onSubmit(code);
      }}
    >
      <label className={labelClass} htmlFor="manual-barcode">
        {t("manual_entry")}
      </label>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          id="manual-barcode"
          type="text"
          inputMode="numeric"
          autoComplete="off"
          value={value}
          placeholder={t("manual_placeholder")}
          aria-invalid={invalid}
          onChange={(e) => setValue(e.target.value)}
          className={`${inputClass} font-mono tracking-wide sm:flex-1`}
        />
        <button type="submit" className={buttonClass()}>
          {t("submit")}
        </button>
      </div>
      {invalid && (
        <p role="alert" className="text-sm text-text-primary">
          {t("invalid")}
        </p>
      )}
    </form>
  );
}
