import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MAX_UPLOAD_BYTES, resizeImage } from "@/features/scan/lib/resizeImage";

// jsdom has no image decoder or canvas encoder: stub both. The encoder returns
// a blob whose size depends on the canvas area and the JPEG quality.
type Canvas = {
  width: number;
  height: number;
  getContext: () => { drawImage: () => void };
  toBlob: (cb: (b: Blob | null) => void, type: string, q: number) => void;
};
let canvases: Canvas[];
let bytesPerPixel: number;
const close = vi.fn();

beforeEach(() => {
  canvases = [];
  bytesPerPixel = 1;
  close.mockReset();
  vi.stubGlobal(
    "createImageBitmap",
    vi.fn(async () => ({ width: 4000, height: 3000, close })),
  );
  const real = document.createElement.bind(document);
  vi.spyOn(document, "createElement").mockImplementation(((tag: string) => {
    if (tag !== "canvas") return real(tag);
    const c: Canvas = {
      width: 0,
      height: 0,
      getContext: () => ({ drawImage: () => {} }),
      toBlob: (cb, type, q) => {
        const size = Math.round(c.width * c.height * bytesPerPixel * q);
        cb(new Blob([new Uint8Array(size)], { type }));
      },
    };
    canvases.push(c);
    return c as unknown as HTMLElement;
  }) as typeof document.createElement);
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const photo = () => new File([new Uint8Array(10)], "label.heic");

describe("resizeImage", () => {
  it("resizeImage output ≤ 8 MB and image/jpeg, longest side ≤ 2000 px", async () => {
    const out = await resizeImage(photo());
    expect(out.type).toBe("image/jpeg");
    expect(out.size).toBeLessThanOrEqual(MAX_UPLOAD_BYTES);
    expect(canvases[0]?.width).toBe(2000);
    expect(canvases[0]?.height).toBe(1500);
    expect(close).toHaveBeenCalled();
  });

  it("lowers quality, then size, until the photo fits in 8 MB", async () => {
    bytesPerPixel = 6; // 2000x1500 at q 0.55 is still ~9.9 MB
    const out = await resizeImage(photo());
    expect(out.size).toBeLessThanOrEqual(MAX_UPLOAD_BYTES);
    expect(out.type).toBe("image/jpeg");
    expect(canvases.length).toBeGreaterThan(1);
    expect(canvases.at(-1)?.width).toBeLessThan(2000);
  });

  it("never upscales a small photo", async () => {
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => ({ width: 800, height: 600, close })),
    );
    await resizeImage(photo());
    expect(canvases[0]?.width).toBe(800);
  });

  it("an undecodable file is unsupported_image", async () => {
    vi.stubGlobal(
      "createImageBitmap",
      vi.fn(async () => {
        throw new DOMException("bad", "InvalidStateError");
      }),
    );
    await expect(resizeImage(photo())).rejects.toMatchObject({
      code: "unsupported_image",
    });
  });
});
