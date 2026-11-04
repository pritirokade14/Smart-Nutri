import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  pickMimeType,
  useVoiceRecorder,
} from "@/features/voice/hooks/useVoiceRecorder";
import { FakeMediaRecorder, installMedia, removeMedia } from "./fakes";

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("pickMimeType", () => {
  it("pickMimeType prefers webm opus then ogg then mp4", () => {
    const all = () => true;
    expect(pickMimeType(all)).toBe("audio/webm;codecs=opus");
    expect(pickMimeType((t) => t !== "audio/webm;codecs=opus")).toBe(
      "audio/ogg;codecs=opus",
    );
    expect(pickMimeType((t) => t === "audio/mp4")).toBe("audio/mp4");
  });

  it("pickMimeType returns null when nothing supported", () => {
    expect(pickMimeType(() => false)).toBeNull();
  });
});

describe("useVoiceRecorder", () => {
  it("start without MediaRecorder sets voice.unsupported_browser", async () => {
    removeMedia();
    const { result } = renderHook(() => useVoiceRecorder({ maxSeconds: 30 }));
    await act(() => result.current.start());
    expect(result.current.state).toMatchObject({
      status: "error",
      errorKey: "voice.unsupported_browser",
    });
  });

  it("no supported audio format is voice.unsupported_browser, and the mic is never opened", async () => {
    const media = installMedia();
    FakeMediaRecorder.supported = new Set();
    const { result } = renderHook(() => useVoiceRecorder({ maxSeconds: 30 }));
    await act(() => result.current.start());
    expect(result.current.state.errorKey).toBe("voice.unsupported_browser");
    expect(media.getUserMedia).not.toHaveBeenCalled();
  });

  it("getUserMedia NotAllowedError sets voice.mic_denied", async () => {
    installMedia("NotAllowedError");
    const { result } = renderHook(() => useVoiceRecorder({ maxSeconds: 30 }));
    await act(() => result.current.start());
    expect(result.current.state).toMatchObject({
      status: "error",
      errorKey: "voice.mic_denied",
    });
    expect(FakeMediaRecorder.instances).toHaveLength(0);
  });

  it("no microphone sets voice.no_mic", async () => {
    installMedia("NotFoundError");
    const { result } = renderHook(() => useVoiceRecorder({ maxSeconds: 30 }));
    await act(() => result.current.start());
    expect(result.current.state.errorKey).toBe("voice.no_mic");
  });

  it("records audio only, then stop returns the clip and releases the mic", async () => {
    vi.useFakeTimers();
    const media = installMedia();
    const { result } = renderHook(() => useVoiceRecorder({ maxSeconds: 30 }));
    await act(() => result.current.start());
    expect(media.getUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(result.current.state.status).toBe("recording");
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });
    expect(result.current.state.elapsedMs).toBeGreaterThanOrEqual(2000);
    let blob: Blob | null = null;
    await act(async () => {
      blob = await result.current.stop();
    });
    expect(blob).not.toBeNull();
    expect((blob as unknown as Blob).type).toBe("audio/webm;codecs=opus");
    expect(result.current.state.status).toBe("idle");
    expect(media.streams[0]?.tracks.every((t) => t.stopped)).toBe(true);
  });

  it("auto-stops at 30 s (fake timers)", async () => {
    vi.useFakeTimers();
    const media = installMedia();
    const onAutoStop = vi.fn();
    const { result } = renderHook(() =>
      useVoiceRecorder({ maxSeconds: 30, onAutoStop }),
    );
    await act(() => result.current.start());
    await act(async () => {
      vi.advanceTimersByTime(29_000);
    });
    expect(onAutoStop).not.toHaveBeenCalled();
    await act(async () => {
      vi.advanceTimersByTime(1_000);
      await Promise.resolve();
    });
    await act(async () => {
      await vi.runAllTimersAsync();
    });
    expect(onAutoStop).toHaveBeenCalledTimes(1);
    expect(onAutoStop.mock.calls[0]?.[0]).toBeInstanceOf(Blob);
    expect(FakeMediaRecorder.instances[0]?.state).toBe("inactive");
    expect(media.streams[0]?.tracks.every((t) => t.stopped)).toBe(true);
  });

  it("a tap shorter than half a second sends nothing", async () => {
    vi.useFakeTimers();
    installMedia();
    const { result } = renderHook(() => useVoiceRecorder({ maxSeconds: 30 }));
    await act(() => result.current.start());
    await act(async () => {
      vi.advanceTimersByTime(200);
    });
    let blob: Blob | null = new Blob();
    await act(async () => {
      blob = await result.current.stop();
    });
    expect(blob).toBeNull();
    expect(result.current.state.errorKey).toBe("voice.not_understood");
  });

  it("cancel drops the clip and releases the mic", async () => {
    const media = installMedia();
    const { result } = renderHook(() => useVoiceRecorder({ maxSeconds: 30 }));
    await act(() => result.current.start());
    act(() => result.current.cancel());
    expect(result.current.state.status).toBe("idle");
    expect(media.streams[0]?.tracks.every((t) => t.stopped)).toBe(true);
  });

  it("unmounting while recording releases the mic", async () => {
    const media = installMedia();
    const { result, unmount } = renderHook(() =>
      useVoiceRecorder({ maxSeconds: 30 }),
    );
    await act(() => result.current.start());
    unmount();
    expect(media.streams[0]?.tracks.every((t) => t.stopped)).toBe(true);
  });
});
