import { BrowserMultiFormatReader } from "@zxing/browser";
import { BarcodeFormat, DecodeHintType } from "@zxing/library";

export type Detector = {
  stop(): void;
  onCode(cb: (code: string) => void): void;
};

const NATIVE_FORMATS = ["ean_13", "ean_8", "upc_a", "upc_e"];
const POLL_MS = 250;

type NativeDetector = {
  detect(v: HTMLVideoElement): Promise<{ rawValue: string }[]>;
};
type NativeCtor = new (o: { formats: string[] }) => NativeDetector;

function stopTracks(video: HTMLVideoElement) {
  const s = video.srcObject;
  if (s && "getTracks" in s) for (const t of s.getTracks()) t.stop();
}

export async function createDetector(
  video: HTMLVideoElement,
): Promise<Detector> {
  const Native = (window as unknown as { BarcodeDetector?: NativeCtor })
    .BarcodeDetector;
  let stopped = false;
  let halt: () => void = () => {};

  if (Native) {
    const det = new Native({ formats: NATIVE_FORMATS });
    let timer: ReturnType<typeof setTimeout> | undefined;
    halt = () => clearTimeout(timer);
    return {
      onCode(cb) {
        const tick = async () => {
          if (stopped) return;
          try {
            const found = await det.detect(video);
            const code = found[0]?.rawValue;
            if (code && !stopped) cb(code);
          } catch {
            // frame not ready; try again
          }
          if (!stopped) timer = setTimeout(tick, POLL_MS);
        };
        tick();
      },
      stop() {
        stopped = true;
        halt();
        stopTracks(video);
      },
    };
  }

  const hints = new Map();
  hints.set(DecodeHintType.POSSIBLE_FORMATS, [
    BarcodeFormat.EAN_13,
    BarcodeFormat.EAN_8,
    BarcodeFormat.UPC_A,
    BarcodeFormat.UPC_E,
  ]);
  const reader = new BrowserMultiFormatReader(hints);
  return {
    onCode(cb) {
      reader
        .decodeFromVideoElement(video, (result) => {
          if (result && !stopped) cb(result.getText());
        })
        .then((controls) => {
          halt = () => controls.stop();
          if (stopped) controls.stop();
        })
        .catch(() => {});
    },
    stop() {
      stopped = true;
      halt();
      stopTracks(video);
    },
  };
}
