"use client";

import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
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
      <p role="alert" className="text-(length:--text-md)">
        {t(error)}
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-(--spacing-2)">
      <video ref={videoRef} playsInline muted className="w-full" />
      <p className="text-(length:--text-sm)">{t("scanning")}</p>
    </div>
  );
}
