"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { track } from "@/lib/analytics";
import { setScanDraft } from "../api/draftCache";
import { type UploadStage, useUploadLabel } from "../api/useUploadLabel";

/**
 * Label photo capture: camera (mobile), file picker, or drag and drop
 * (desktop). Uploads, extracts, then opens the confirm step. Every error
 * offers Retake and Enter manually; no draft form is shown on error.
 */
export function LabelUpload({ barcode }: { barcode: string | null }) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const client = useQueryClient();
  const uid = useId();
  const cameraRef = useRef<HTMLInputElement>(null);
  const [stage, setStage] = useState<UploadStage>("uploading");
  const [dragging, setDragging] = useState(false);
  const upload = useUploadLabel({ onStage: setStage });
  const q = barcode ? `?barcode=${encodeURIComponent(barcode)}` : "";

  const start = (file: File | undefined) => {
    if (!file || upload.isPending) return;
    track("label_scan_started");
    upload.mutate(barcode ? { file, barcode } : { file }, {
      onSuccess: (scan) => {
        setScanDraft(client, scan, barcode);
        router.push(`/${locale}/scan/confirm/${scan.scan_id}`);
      },
    });
  };

  const retake = () => {
    upload.reset();
    cameraRef.current?.click();
  };

  const btn =
    "inline-block cursor-pointer rounded-(--radius-md) border px-(--spacing-4) py-(--spacing-2) text-(length:--text-md)";

  let body: React.ReactNode;
  if (upload.isPending || upload.isSuccess) {
    body = (
      <p role="status" className="text-(length:--text-md)">
        {stage === "reading" ? t("label.reading") : t("label.uploading")}
      </p>
    );
  } else if (upload.isError) {
    const key = `error.${upload.error.code}`;
    body = (
      <section className="space-y-(--spacing-3)">
        <p role="alert" className="text-(length:--text-md)">
          {t.has(key) ? t(key) : t("error.internal_error")}
        </p>
        <div className="flex flex-wrap gap-(--spacing-2)">
          <button type="button" onClick={retake} className={btn}>
            {t("label.retake")}
          </button>
          <a href={`/${locale}/scan/manual${q}`} className={btn}>
            {t("label.enter_manually")}
          </a>
        </div>
      </section>
    );
  } else {
    body = (
      <section className="space-y-(--spacing-3)">
        <div className="flex flex-wrap gap-(--spacing-2)">
          <label htmlFor={`${uid}-camera`} className={btn}>
            {t("label.take_photo")}
          </label>
          <label htmlFor={`${uid}-file`} className={btn}>
            {t("label.choose_file")}
          </label>
        </div>
        {/* Desktop: drop a photo anywhere in this zone. */}
        <section
          aria-label={t("label.drop_here")}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const file = Array.from(e.dataTransfer.files).find((f) =>
              f.type.startsWith("image/"),
            );
            start(file);
          }}
          className={`rounded-(--radius-lg) border-2 border-dashed p-(--spacing-6) text-center text-(length:--text-md) ${dragging ? "border-(--color-text-primary)" : ""}`}
        >
          <p>{t("label.drop_here")}</p>
        </section>
        <a href={`/${locale}/scan/manual${q}`} className={btn}>
          {t("label.enter_manually")}
        </a>
      </section>
    );
  }

  return (
    <main className="mx-auto flex max-w-xl flex-col gap-(--spacing-4) p-(--spacing-4)">
      <h1 className="text-(length:--text-xl)">{t("label.title")}</h1>
      {/* Inputs stay mounted so Retake can reopen the camera. */}
      <input
        ref={cameraRef}
        id={`${uid}-camera`}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        aria-label={t("label.take_photo")}
        onChange={(e) => {
          start(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      <input
        id={`${uid}-file`}
        type="file"
        accept="image/*"
        className="sr-only"
        aria-label={t("label.choose_file")}
        onChange={(e) => {
          start(e.target.files?.[0]);
          e.target.value = "";
        }}
      />
      {body}
      <p className="text-(length:--text-sm)">{t("common.disclaimer")}</p>
    </main>
  );
}
