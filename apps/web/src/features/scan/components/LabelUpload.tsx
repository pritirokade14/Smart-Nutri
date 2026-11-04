"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { pageClass } from "@/components/shell/page";
import { buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { ErrorState } from "@/components/ui/ErrorState";
import { CameraIcon, PencilIcon, UploadIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Skeleton } from "@/components/ui/Skeleton";
import { track } from "@/lib/analytics";
import { setScanDraft } from "../api/draftCache";
import { type UploadStage, useUploadLabel } from "../api/useUploadLabel";
import { imageQualityReasons } from "../lib/warnings";

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
    // Event names only, no properties: no label content or health data.
    track("scan_started", { method: "label" });
    upload.mutate(barcode ? { file, barcode } : { file }, {
      onSuccess: (scan) => {
        setScanDraft(client, scan, barcode);
        router.push(`/${locale}/scan/confirm/${scan.scan_id}`);
      },
      onError: () => track("scan_completed", { method: "label", found: false }),
    });
  };

  const retake = () => {
    upload.reset();
    cameraRef.current?.click();
  };

  const btn = buttonClass({ variant: "outline" });

  let body: React.ReactNode;
  if (upload.isPending || upload.isSuccess) {
    body = (
      <Card className="flex flex-col items-center gap-4 py-10 text-center">
        <span className="flex size-16 items-center justify-center rounded-full bg-brand-soft text-brand-primary">
          <UploadIcon className="size-8 animate-pulse motion-reduce:animate-none" />
        </span>
        <p role="status" className="text-md font-medium text-text-primary">
          {stage === "reading" ? t("label.reading") : t("label.uploading")}
        </p>
        <Skeleton className="h-2 w-40 rounded-full" />
      </Card>
    );
  } else if (upload.isError) {
    const key = `error.${upload.error.code}`;
    // Label v2: an unreadable photo (no extraction was tried) gets a retake
    // prompt with one concrete fix per reason the API found.
    const quality = upload.error.code === "image_quality_low";
    const reasons = quality ? imageQualityReasons(upload.error.details) : [];
    body = (
      <ErrorState
        message={
          quality
            ? t("image_quality.title")
            : t.has(key)
              ? t(key)
              : t("error.internal_error")
        }
      >
        {quality ? (
          <ul data-testid="retake-hints" className="w-full space-y-1">
            {(reasons.length > 0 ? reasons : (["generic"] as const)).map(
              (r) => (
                <li key={r} className="text-md text-text-primary">
                  {t(
                    r === "generic"
                      ? "image_quality.hint_generic"
                      : `image_quality.${r}`,
                  )}
                </li>
              ),
            )}
          </ul>
        ) : null}
        <button type="button" onClick={retake} className={btn}>
          <CameraIcon />
          {t("label.retake")}
        </button>
        <a href={`/${locale}/scan/manual${q}`} className={btn}>
          <PencilIcon />
          {t("label.enter_manually")}
        </a>
      </ErrorState>
    );
  } else {
    body = (
      <>
        <div className="grid gap-3 sm:grid-cols-2">
          <label
            htmlFor={`${uid}-camera`}
            className={buttonClass({ size: "lg" })}
          >
            <CameraIcon />
            {t("label.take_photo")}
          </label>
          <label
            htmlFor={`${uid}-file`}
            className={buttonClass({ variant: "outline", size: "lg" })}
          >
            <UploadIcon />
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
            // Any dropped file goes through the resize step, which rejects
            // HEIC and non-images with unsupported_image before upload.
            start(e.dataTransfer.files[0]);
          }}
          className={`flex flex-col items-center gap-3 rounded-lg border-2 border-dashed p-8 text-center text-md text-text-secondary transition-colors max-sm:hidden ${dragging ? "border-brand-primary bg-brand-soft" : "border-border-default bg-surface-default"}`}
        >
          <UploadIcon className="size-8" />
          <p>{t("label.drop_here")}</p>
        </section>
        <a
          href={`/${locale}/scan/manual${q}`}
          className={buttonClass({ variant: "ghost", className: "self-start" })}
        >
          <PencilIcon />
          {t("label.enter_manually")}
        </a>
      </>
    );
  }

  return (
    <main className={`${pageClass} flex flex-col`}>
      <SectionHeader as="h1" title={t("label.title")} />
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
      <DisclaimerFooter />
    </main>
  );
}
