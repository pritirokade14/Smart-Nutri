"use client";

import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { CameraIcon, ScanIcon } from "@/components/ui/icons";
import { normalizeBarcode } from "../lib/barcode";
import { createDetector } from "../lib/detector";

type CamError = "camera_denied" | "camera_unavailable" | null;

export function BarcodeScanner({ onCode }: { onCode: (code: string) => void }) {
  const t = useTranslations("scan");
  const videoRef = useRef<HTMLVideoElement>(null);
  const onCodeRef = useRef(onCode);
  onCodeRef.current = onCode;
  const [error, setError] = useState<CamError>(null);

  useEffect(() => {
    let cancelled = false;
    let fired = false;
    let stop: (() => void) | undefined;
    let stream: MediaStream | undefined;

    (async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        });
        const video = videoRef.current;
        if (cancelled || !video) {
          for (const tr of stream.getTracks()) tr.stop();
          return;
        }
        video.srcObject = stream;
        await video.play().catch(() => {});
        const det = await createDetector(video);
        stop = () => det.stop();
        if (cancelled) return det.stop();
        det.onCode((raw) => {
          const code = normalizeBarcode(raw);
          if (!code || fired || cancelled) return;
          fired = true;
          det.stop();
          onCodeRef.current(code);
        });
      } catch (e) {
        if (cancelled) return;
        const name = e instanceof DOMException ? e.name : "";
        setError(
          name === "NotAllowedError" || name === "SecurityError"
            ? "camera_denied"
            : "camera_unavailable",
        );
      }
    })();

    return () => {
      cancelled = true;
      stop?.();
      if (stream) for (const tr of stream.getTracks()) tr.stop();
    };
  }, []);

  if (error) {
    return (
      <div className="flex items-start gap-3 p-4 sm:p-5">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-surface-muted text-text-secondary">
          <CameraIcon />
        </span>
        <p role="alert" className="pt-2 text-md text-text-primary">
          {t(error)}
        </p>
      </div>
    );
  }
  return (
    <div className="flex flex-col">
      <div className="relative aspect-[4/3] w-full overflow-hidden bg-surface-muted">
        <video
          ref={videoRef}
          playsInline
          muted
          className="h-full w-full object-cover"
        />
        {/* Aiming frame (decorative). */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-8 top-1/2 h-1/3 -translate-y-1/2 rounded-lg border-2 border-brand-on shadow-sm"
        />
      </div>
      <p className="flex items-center gap-2 px-4 py-3 text-sm text-text-secondary">
        <ScanIcon className="size-4 shrink-0" />
        {t("scanning")}
      </p>
    </div>
  );
}
