import { afterEach, describe, expect, it, vi } from "vitest";

const zx = vi.hoisted(() => ({
  decode: vi.fn(),
  stop: vi.fn(),
  ctor: vi.fn(),
}));
vi.mock("@zxing/browser", () => ({
  BrowserMultiFormatReader: class {
    constructor(...a: unknown[]) {
      zx.ctor(...a);
    }
    decodeFromVideoElement = async (_v: unknown, cb: unknown) => {
      zx.decode(cb);
      return { stop: zx.stop };
    };
  },
}));

import { createDetector } from "@/features/scan/lib/detector";

function video() {
  const track = { stop: vi.fn() };
  const v = document.createElement("video");
  Object.defineProperty(v, "srcObject", {
    value: { getTracks: () => [track] },
    writable: true,
  });
  return { v, track };
}

afterEach(() => {
  // biome-ignore lint/suspicious/noExplicitAny: test cleanup
  delete (window as any).BarcodeDetector;
  vi.clearAllMocks();
});

describe("createDetector", () => {
  it("uses BarcodeDetector when present", async () => {
    const detect = vi.fn().mockResolvedValue([{ rawValue: "8901063201089" }]);
    const Ctor = vi.fn(function (this: object) {
      Object.assign(this, { detect });
    });
    // biome-ignore lint/suspicious/noExplicitAny: test stub
    (window as any).BarcodeDetector = Ctor;
    const { v, track } = video();
    const d = await createDetector(v);
    const got = new Promise<string>((res) => d.onCode(res));
    expect(await got).toBe("8901063201089");
    expect(Ctor).toHaveBeenCalledWith({
      formats: ["ean_13", "ean_8", "upc_a", "upc_e"],
    });
    expect(zx.ctor).not.toHaveBeenCalled();
    d.stop();
    expect(track.stop).toHaveBeenCalled();
  });

  it("falls back to zxing when BarcodeDetector is missing", async () => {
    const { v, track } = video();
    const d = await createDetector(v);
    const cb = vi.fn();
    d.onCode(cb);
    expect(zx.ctor).toHaveBeenCalled();
    const handler = zx.decode.mock.calls[0]?.[0];
    handler({ getText: () => "12345670" }, undefined);
    handler(undefined, new Error("not found"));
    expect(cb).toHaveBeenCalledTimes(1);
    expect(cb).toHaveBeenCalledWith("12345670");
    await Promise.resolve();
    await Promise.resolve();
    d.stop();
    expect(zx.stop).toHaveBeenCalled();
    expect(track.stop).toHaveBeenCalled();
  });
});
