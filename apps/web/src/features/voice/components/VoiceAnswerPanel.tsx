"use client";

import { useTranslations } from "next-intl";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { VerdictBadge } from "@/components/ui/VerdictBadge";
import { toneOf } from "@/components/ui/verdict-tone";
import type { VoiceAnswer } from "../api/askVoice";

/**
 * A voice answer: the engine's status (as sent; anything unexpected is
 * unknown grey, never ok), the answer text (it starts with the engine's
 * verdict sentence), the spoken reply, and the disclaimer. The transcript is
 * shown back but never stored.
 */
export function VoiceAnswerPanel({ answer }: { answer: VoiceAnswer }) {
  const t = useTranslations();
  const status = toneOf(answer.verdict_status);
  return (
    <section
      data-testid="voice-answer"
      data-verdict={status}
      aria-label={t("voice.answer_title")}
      className="space-y-3 rounded-md border border-s-4 border-border-default border-s-(--verdict-color) bg-surface-default p-3"
    >
      <VerdictBadge status={status} />
      <p className="text-sm text-text-secondary">
        {t("voice.you_asked", { question: answer.question })}
      </p>
      <p className="text-md whitespace-pre-line text-text-primary">
        {answer.answer}
      </p>
      {answer.source === "fallback" ? (
        <p className="text-sm text-text-secondary">
          {t("explanation.source_fallback_note")}
        </p>
      ) : null}
      {/* biome-ignore lint/a11y/useMediaCaption: the answer text above is the transcript */}
      <audio
        controls
        autoPlay
        src={answer.audio_url}
        preload="auto"
        className="w-full"
      />
      <DisclaimerFooter />
    </section>
  );
}
