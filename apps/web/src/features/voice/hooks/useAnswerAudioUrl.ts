"use client";

import { useEffect, useState } from "react";
import type { VoiceAnswer } from "../api/askVoice";

/** The base64 mp3 as bytes, or null when it is missing or malformed. */
export function decodeAnswerAudio(base64: string | null): Uint8Array | null {
  if (!base64) return null;
  try {
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
  } catch {
    return null;
  }
}

/**
 * A Blob URL for the answer's inline mp3 (`audio_base64`), or null when the
 * answer is text only. The audio is never stored (ADR 0020): it lives in
 * memory, and the URL is revoked when the answer closes or changes.
 */
export function useAnswerAudioUrl(answer: VoiceAnswer): string | null {
  const [url, setUrl] = useState<string | null>(null);
  const { audio_base64: base64, audio_mime: mime } = answer;
  useEffect(() => {
    const bytes = decodeAnswerAudio(base64);
    if (!bytes) {
      setUrl(null);
      return;
    }
    const made = URL.createObjectURL(
      new Blob([bytes as BlobPart], { type: mime }),
    );
    setUrl(made);
    return () => {
      URL.revokeObjectURL(made);
      setUrl(null);
    };
  }, [base64, mime]);
  return url;
}
