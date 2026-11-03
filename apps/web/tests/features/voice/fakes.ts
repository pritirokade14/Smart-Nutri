import { vi } from "vitest";

// Browser recording stand-ins: a MediaRecorder that emits one chunk on stop,
// and media streams whose tracks record whether they were stopped.

export class FakeTrack {
  stopped = false;
  stop() {
    this.stopped = true;
  }
}

export class FakeStream {
  tracks = [new FakeTrack()];
  getTracks() {
    return this.tracks;
  }
}

export class FakeMediaRecorder {
  static supported = new Set(["audio/webm;codecs=opus"]);
  static instances: FakeMediaRecorder[] = [];
  static isTypeSupported(t: string) {
    return FakeMediaRecorder.supported.has(t);
  }
  state: "inactive" | "recording" = "inactive";
  mimeType: string;
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  constructor(
    public stream: FakeStream,
    opts: { mimeType: string },
  ) {
    this.mimeType = opts.mimeType;
    FakeMediaRecorder.instances.push(this);
  }
  start() {
    this.state = "recording";
  }
  stop() {
    this.state = "inactive";
    this.ondataavailable?.({
      data: new Blob([new Uint8Array([0x1a, 0x45, 0xdf, 0xa3, 1, 2, 3])], {
        type: this.mimeType,
      }),
    });
    queueMicrotask(() => this.onstop?.());
  }
}

export type MediaSetup = {
  getUserMedia: ReturnType<typeof vi.fn>;
  streams: FakeStream[];
};

/** Installs MediaRecorder and navigator.mediaDevices; `deny` makes getUserMedia fail. */
export function installMedia(deny?: string): MediaSetup {
  FakeMediaRecorder.instances = [];
  FakeMediaRecorder.supported = new Set(["audio/webm;codecs=opus"]);
  const streams: FakeStream[] = [];
  const getUserMedia = vi.fn(async () => {
    if (deny) throw new DOMException("no", deny);
    const s = new FakeStream();
    streams.push(s);
    return s;
  });
  vi.stubGlobal("MediaRecorder", FakeMediaRecorder);
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: { getUserMedia },
  });
  return { getUserMedia, streams };
}

export function removeMedia() {
  vi.stubGlobal("MediaRecorder", undefined);
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: undefined,
  });
}
