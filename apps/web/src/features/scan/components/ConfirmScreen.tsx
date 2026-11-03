"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import { removeScanDraft, useScanDraft } from "../api/draftCache";
import { useSaveDraft } from "../api/useSaveDraft";
import type { ProductCreate } from "../lib/draftSchema";
import { DraftForm, type ServerFieldError } from "./DraftForm";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function fieldErrors(error: ApiError | null): ServerFieldError | null {
  if (!error) return null;
  if (error.code !== "implausible_value" && error.code !== "validation_error")
    return null;
  const fields = Array.isArray(error.details.fields)
    ? (error.details.fields as unknown[]).filter(
        (f): f is string => typeof f === "string",
      )
    : [];
  return { code: error.code, fields };
}

function existingProductId(error: ApiError | null): string | null {
  if (error?.code !== "product_exists") return null;
  const id = error.details.product_id;
  return typeof id === "string" && UUID.test(id) ? id : null;
}

/** Retake and Enter manually: offered on every state of the confirm step. */
export function ScanExits({ barcode }: { barcode: string | null }) {
  const t = useTranslations("label");
  const locale = useLocale();
  const q = barcode ? `?barcode=${encodeURIComponent(barcode)}` : "";
  const cls =
    "inline-block rounded-(--radius-md) border px-(--spacing-4) py-(--spacing-2) text-(length:--text-md)";
  return (
    <nav className="flex flex-wrap gap-(--spacing-2)">
      <a href={`/${locale}/scan/label${q}`} className={cls}>
        {t("retake")}
      </a>
      <a href={`/${locale}/scan/manual${q}`} className={cls}>
        {t("enter_manually")}
      </a>
    </nav>
  );
}

/**
 * The label-confirm step. With a scan id, the draft comes from memory (the
 * upload page put it there); without one, it is an empty manual-entry form.
 * Saving creates the product, then opens its result view (which analyses it).
 */
export function ConfirmScreen({
  scanId,
  barcode = null,
}: {
  scanId: string | null;
  barcode?: string | null;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const client = useQueryClient();
  const [savedId, setSavedId] = useState<string | null>(null);

  // The draft is dropped once saved, after the form (its only reader) is gone.
  useEffect(() => {
    if (savedId && scanId) removeScanDraft(client, scanId);
  }, [savedId, scanId, client]);

  if (savedId) {
    return (
      <main className="mx-auto max-w-xl space-y-(--spacing-4) p-(--spacing-4)">
        <p role="status" className="text-(length:--text-md)">
          {t("common.loading")}
        </p>
      </main>
    );
  }
  return (
    <DraftStep
      scanId={scanId}
      barcode={barcode}
      onSaved={(productId) => {
        // Event names only: no label content or health data.
        track(scanId ? "label_scan_saved" : "manual_product_saved");
        setSavedId(productId);
        router.push(`/${locale}/product/${productId}`);
      }}
    />
  );
}

function DraftStep({
  scanId,
  barcode,
  onSaved,
}: {
  scanId: string | null;
  barcode: string | null;
  onSaved(productId: string): void;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const draft = useScanDraft(scanId);
  const save = useSaveDraft();
  const code = draft.data?.barcode ?? barcode ?? null;

  const onSave = (body: ProductCreate) =>
    save.mutate(body, {
      onSuccess: (product) => {
        if (product.product_id) onSaved(product.product_id);
      },
    });

  let body: React.ReactNode;
  if (scanId !== null && draft.isPending) {
    body = (
      <p role="status" className="text-(length:--text-md)">
        {t("common.loading")}
      </p>
    );
  } else if (scanId !== null && draft.isError) {
    body = (
      <p role="alert" className="text-(length:--text-md)">
        {t("error.scan_not_found")}
      </p>
    );
  } else {
    const error = save.error;
    const missingId = save.isSuccess && !save.data.product_id;
    const existing = existingProductId(error);
    const message = error
      ? t.has(`error.${error.code}`)
        ? t(`error.${error.code}`)
        : t("error.internal_error")
      : missingId
        ? t("error.internal_error")
        : null;
    body = (
      <>
        {message ? (
          <section className="space-y-(--spacing-2)">
            <p role="alert" className="text-(length:--text-md)">
              {message}
            </p>
            {existing ? (
              <a
                href={`/${locale}/product/${existing}`}
                className="inline-block rounded-(--radius-md) border px-(--spacing-4) py-(--spacing-2) text-(length:--text-md) underline"
              >
                {t("confirm.open_existing")}
              </a>
            ) : null}
          </section>
        ) : null}
        <DraftForm
          scan={
            scanId !== null && draft.data
              ? {
                  scanId: draft.data.scan.scan_id,
                  draft: draft.data.scan.draft,
                }
              : null
          }
          barcode={code}
          busy={save.isPending}
          serverError={fieldErrors(error)}
          onSave={onSave}
        />
      </>
    );
  }

  return (
    <main className="mx-auto max-w-xl space-y-(--spacing-4) p-(--spacing-4)">
      <ScanExits barcode={code} />
      {body}
    </main>
  );
}
