"use client";

import { useTranslations } from "next-intl";
import { buttonClass } from "@/components/ui/Button";
import type { RecorderState } from "../hooks/useVoiceRecorder";

/**
 * Press and hold to ask; release sends, sliding off cancels. Keyboard: Space
 * starts, Space again sends (Escape cancels). A timer shows while recording.
 */
export function PushToTalkButton({
  status,
  elapsedMs,
  onStart,
  onStop,
  onCancel,
}: {
  status: RecorderState["status"];
  elapsedMs: number;
  onStart: () => void;
  onStop: () => void;
  onCancel: () => void;
}) {
  const t = useTranslations("voice");
  const recording = status === "recording";
  const busy = status === "uploading";
  return (
    <div className="space-y-1">
      <button
        type="button"
        aria-pressed={recording}
        disabled={busy}
        onPointerDown={(e) => {
          if (e.button !== undefined && e.button !== 0) return;
          if (!recording) onStart();
        }}
        onPointerUp={() => {
          if (recording) onStop();
        }}
        onPointerLeave={() => {
          if (recording) onCancel();
        }}
        onPointerCancel={() => {
          if (recording) onCancel();
        }}
        onContextMenu={(e) => e.preventDefault()}
        onKeyDown={(e) => {
          if (e.key === " " || e.key === "Spacebar") {
            e.preventDefault();
            if (e.repeat) return;
            if (recording) onStop();
            else onStart();
          } else if (e.key === "Escape" && recording) onCancel();
        }}
        className={buttonClass({
          variant: recording ? "primary" : "outline",
          size: "sm",
          className: "touch-none select-none",
        })}
      >
        {t("button_hold")}
      </button>
      {recording ? (
        <p role="status" className="text-sm text-text-secondary">
          <span>{t("recording")}</span>{" "}
          <span>{t("elapsed", { seconds: Math.floor(elapsedMs / 1000) })}</span>
        </p>
      ) : busy ? (
        <p role="status" className="text-sm text-text-secondary">
          {t("thinking")}
        </p>
      ) : null}
    </div>
  );
}
