"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type RecorderState = {
  status: "idle" | "recording" | "uploading" | "playing" | "error";
  elapsedMs: number;
  errorKey?: string;
};

// Opus first (small, and the API transcodes it), then AAC in MP4 (Safari).
const MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/ogg;codecs=opus",
  "audio/mp4",
] as const;

/** Shorter than this is a tap, not a question: nothing is sent. */
const MIN_MS = 500;
const TICK_MS = 200;

export function pickMimeType(
  isTypeSupported: (t: string) => boolean,
): string | null {
  return MIME_TYPES.find((t) => isTypeSupported(t)) ?? null;
}

function micErrorKey(e: unknown): string {
  const name = e instanceof DOMException ? e.name : "";
  if (name === "NotFoundError" || name === "OverconstrainedError")
    return "voice.no_mic";
  if (name === "NotAllowedError" || name === "SecurityError")
    return "voice.mic_denied";
  return "voice.unsupported_browser";
}

type Session = {
  recorder: MediaRecorder;
  stream: MediaStream;
  chunks: Blob[];
  startedAt: number;
  timer: ReturnType<typeof setInterval>;
};

/**
 * Push-to-talk recording with MediaRecorder (F10): audio only, at most
 * `maxSeconds` (then it stops by itself and hands the clip to `onAutoStop`).
 * The microphone is released whenever recording ends, is cancelled or the
 * component unmounts. Nothing is stored: the clip lives only in memory.
 */
export function useVoiceRecorder(opts: {
  maxSeconds: number;
  onAutoStop?: (clip: Blob) => void;
}): {
  state: RecorderState;
  start(): Promise<void>;
  stop(): Promise<Blob | null>;
  cancel(): void;
} {
  const [state, setState] = useState<RecorderState>({
    status: "idle",
    elapsedMs: 0,
  });
  const session = useRef<Session | null>(null);
  const onAutoStop = useRef(opts.onAutoStop);
  onAutoStop.current = opts.onAutoStop;
  const maxMs = opts.maxSeconds * 1000;

  const release = useCallback((s: Session) => {
    clearInterval(s.timer);
    for (const t of s.stream.getTracks()) t.stop();
    if (session.current === s) session.current = null;
  }, []);

  const finish = useCallback(
    (s: Session): Promise<Blob | null> =>
      new Promise((resolve) => {
        const elapsed = Date.now() - s.startedAt;
        s.recorder.onstop = () => {
          release(s);
          if (elapsed < MIN_MS) {
            setState({
              status: "error",
              elapsedMs: 0,
              errorKey: "voice.not_understood",
            });
            resolve(null);
            return;
          }
          setState({ status: "idle", elapsedMs: 0 });
          resolve(new Blob(s.chunks, { type: s.recorder.mimeType }));
        };
        if (s.recorder.state === "inactive")
          s.recorder.onstop?.(new Event("stop"));
        else s.recorder.stop();
      }),
    [release],
  );

  const start = useCallback(async () => {
    if (session.current) return;
    const Recorder = globalThis.MediaRecorder;
    const media = globalThis.navigator?.mediaDevices;
    const mime =
      Recorder && typeof Recorder.isTypeSupported === "function"
        ? pickMimeType((t) => Recorder.isTypeSupported(t))
        : null;
    if (!Recorder || !media?.getUserMedia || !mime) {
      setState({
        status: "error",
        elapsedMs: 0,
        errorKey: "voice.unsupported_browser",
      });
      return;
    }
    let stream: MediaStream;
    try {
      stream = await media.getUserMedia({ audio: true });
    } catch (e) {
      setState({ status: "error", elapsedMs: 0, errorKey: micErrorKey(e) });
      return;
    }
    const recorder = new Recorder(stream, { mimeType: mime });
    const chunks: Blob[] = [];
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };
    const startedAt = Date.now();
    const s: Session = {
      recorder,
      stream,
      chunks,
      startedAt,
      timer: setInterval(() => {
        const elapsedMs = Date.now() - startedAt;
        if (elapsedMs >= maxMs) {
          void finish(s).then((clip) => {
            if (clip) onAutoStop.current?.(clip);
          });
          clearInterval(s.timer);
          return;
        }
        setState({ status: "recording", elapsedMs });
      }, TICK_MS),
    };
    session.current = s;
    recorder.start();
    setState({ status: "recording", elapsedMs: 0 });
  }, [finish, maxMs]);

  const stop = useCallback(async () => {
    const s = session.current;
    if (!s) return null;
    return finish(s);
  }, [finish]);

  const cancel = useCallback(() => {
    const s = session.current;
    if (s) {
      s.recorder.onstop = null;
      if (s.recorder.state !== "inactive") s.recorder.stop();
      release(s);
    }
    setState({ status: "idle", elapsedMs: 0 });
  }, [release]);

  useEffect(
    () => () => {
      const s = session.current;
      if (!s) return;
      s.recorder.onstop = null;
      if (s.recorder.state !== "inactive") s.recorder.stop();
      release(s);
    },
    [release],
  );

  return { state, start, stop, cancel };
}
