"use client";

import { useMutation } from "@tanstack/react-query";
import { hasLocale, useLocale, useTranslations } from "next-intl";
import { routing } from "@/i18n/routing";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import {
  type AskVoiceArgs,
  askVoice,
  type VoiceAnswer,
  voiceErrorKey,
} from "../api/askVoice";
import { useVoiceRecorder } from "../hooks/useVoiceRecorder";
import { PushToTalkButton } from "./PushToTalkButton";
import { VoiceAnswerPanel } from "./VoiceAnswerPanel";

export type VoiceProductRef = { productId: string } | { barcode: string };

/** Behind NEXT_PUBLIC_FEATURE_VOICE (default off; the API has VOICE_ENABLED off). */
export function isVoiceEnabled(): boolean {
  return process.env.NEXT_PUBLIC_FEATURE_VOICE === "true";
}

/**
 * Push-to-talk for one member on one product (F10): record, send, then show
 * and play the answer. One question at a time; nothing is kept once the
 * page is left.
 */
export function VoiceAsk({
  memberId,
  product,
}: {
  memberId: string;
  product: VoiceProductRef;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const language = hasLocale(routing.locales, locale)
    ? locale
    : routing.defaultLocale;
  const ask = useMutation<VoiceAnswer, ApiError, Blob>({
    mutationFn: (audio) =>
      askVoice({ audio, memberId, language, ...product } as AskVoiceArgs),
    retry: false,
    onSuccess: () => track("voice_asked", { language }),
  });
  const send = (clip: Blob | null) => {
    if (clip) ask.mutate(clip);
  };
  const recorder = useVoiceRecorder({ maxSeconds: 30, onAutoStop: send });
  const status = ask.isPending ? "uploading" : recorder.state.status;

  const errorKey = ask.isError
    ? voiceErrorKey(ask.error)
    : recorder.state.errorKey;
  const message =
    errorKey && t.has(errorKey)
      ? t(errorKey)
      : errorKey
        ? t("error.internal_error")
        : null;

  return (
    <div className="space-y-2" data-testid="voice-ask">
      <PushToTalkButton
        status={status}
        elapsedMs={recorder.state.elapsedMs}
        onStart={() => {
          ask.reset();
          void recorder.start();
        }}
        onStop={() => void recorder.stop().then(send)}
        onCancel={recorder.cancel}
      />
      {message && status !== "recording" ? (
        <p role="alert" className="text-sm text-text-primary">
          {message}
        </p>
      ) : null}
      {ask.data ? <VoiceAnswerPanel answer={ask.data} /> : null}
    </div>
  );
}
