import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  isSupportedImage,
  MAX_UPLOAD_BYTES,
  resizeImage,
} from "@/features/scan/lib/resizeImage";

// jsdom has no image decoder or canvas encoder: stub them. The photo has a
// displayed size (read through <img>); createImageBitmap honours the resize
// options like a browser does (one side given → the other keeps the ratio).
// The encoder returns a blob whose size depends on canvas area and quality.
type Canvas = {
  width: number;
  height: number;
  getContext: () => { drawImage: () => void };
  toBlob: (cb: (b: Blob | null) => void, type: string, q: number) => void;
};
let canvases: Canvas[];
let bytesPerPixel: number;
let photoSize: { width: number; height: number } | null;
const close = vi.fn();
const bitmap = vi.fn(async (_file: Blob, o: ImageBitmapOptions = {}) => {
  if (!photoSize) throw new DOMException("bad", "InvalidStateError");
  const { width: w, height: h } = photoSize;
  let width = w;
  let height = h;
  if (o.resizeWidth) {
    width = o.resizeWidth;
    height = o.resizeHeight ?? Math.round((h * o.resizeWidth) / w);
  } else if (o.resizeHeight) {
    height = o.resizeHeight;
    width = Math.round((w * o.resizeHeight) / h);
  }
  return { width, height, close };
});

class FakeImage {
  onload: (() => void) | null = null;
  onerror: (() => void) | null = null;
  naturalWidth = 0;
  naturalHeight = 0;
  set src(_: string) {
    queueMicrotask(() => {
      if (!photoSize) return this.onerror?.();
      this.naturalWidth = photoSize.width;
      this.naturalHeight = photoSize.height;
      this.onload?.();
    });
  }
}

beforeEach(() => {
  canvases = [];
  bytesPerPixel = 1;
  photoSize = { width: 4000, height: 3000 };
  close.mockReset();
  bitmap.mockClear();
  vi.stubGlobal("createImageBitmap", bitmap);
  vi.stubGlobal("Image", FakeImage);
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:photo");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
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

const photo = (name = "label.jpg", type = "image/jpeg") =>
  new File([new Uint8Array(10)], name, { type });

describe("resizeImage", () => {
  it("output ≤ 8 MB and image/jpeg, longest side ≤ 2000 px", async () => {
    const out = await resizeImage(photo());
    expect(out.type).toBe("image/jpeg");
    expect(out.size).toBeLessThanOrEqual(MAX_UPLOAD_BYTES);
    expect(canvases[0]?.width).toBe(2000);
    expect(canvases[0]?.height).toBe(1500);
    expect(close).toHaveBeenCalled();
  });

  it("decodes straight to the target size, keeping EXIF orientation", async () => {
    await resizeImage(photo());
    expect(bitmap).toHaveBeenCalledTimes(1);
    expect(bitmap.mock.calls[0]?.[1]).toEqual({
      imageOrientation: "from-image",
      resizeQuality: "high",
      resizeWidth: 2000,
    });
  });

  it("a portrait photo is capped on its height", async () => {
    photoSize = { width: 3000, height: 4000 };
    await resizeImage(photo());
    expect(bitmap.mock.calls[0]?.[1]).toEqual({
      imageOrientation: "from-image",
      resizeQuality: "high",
      resizeHeight: 2000,
    });
    expect(canvases[0]?.width).toBe(1500);
    expect(canvases[0]?.height).toBe(2000);
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
    photoSize = { width: 800, height: 600 };
    await resizeImage(photo());
    expect(bitmap.mock.calls[0]?.[1]).toEqual({
      imageOrientation: "from-image",
    });
    expect(canvases[0]?.width).toBe(800);
  });

  it("an undecodable file is unsupported_image", async () => {
    photoSize = null;
    await expect(resizeImage(photo())).rejects.toMatchObject({
      code: "unsupported_image",
    });
  });

  it.each([
    ["label.heic", "image/heic"],
    ["label.HEIF", ""],
    ["label.jpg", "image/heif"],
    ["notes.pdf", "application/pdf"],
  ])("%s (%s) is unsupported_image without decoding", async (name, type) => {
    await expect(resizeImage(photo(name, type))).rejects.toMatchObject({
      code: "unsupported_image",
    });
    expect(bitmap).not.toHaveBeenCalled();
    expect(isSupportedImage(photo(name, type))).toBe(false);
  });

  it("an untyped non-HEIC file goes to the decoder", () => {
    expect(isSupportedImage(photo("IMG_0001", ""))).toBe(true);
    expect(isSupportedImage(photo("label.png", "image/png"))).toBe(true);
  });
});
