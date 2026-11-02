"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
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
      className="flex flex-col gap-(--spacing-2)"
      onSubmit={(e) => {
        e.preventDefault();
        const code = normalizeBarcode(value);
        setInvalid(code === null);
        if (code) onSubmit(code);
      }}
    >
      <label className="text-(length:--text-md)" htmlFor="manual-barcode">
        {t("manual_entry")}
      </label>
      <input
        id="manual-barcode"
        type="text"
        inputMode="numeric"
        autoComplete="off"
        value={value}
        placeholder={t("manual_placeholder")}
        aria-invalid={invalid}
        onChange={(e) => setValue(e.target.value)}
        className="border p-(--spacing-2)"
      />
      {invalid && (
        <p role="alert" className="text-(length:--text-sm)">
          {t("invalid")}
        </p>
      )}
      <button type="submit" className="border p-(--spacing-2)">
        {t("submit")}
      </button>
    </form>
  );
}
