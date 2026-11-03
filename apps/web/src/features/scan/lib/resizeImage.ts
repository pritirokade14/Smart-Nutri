import { ApiError } from "@/lib/api/errors";

/** The API's upload limit (413 image_too_large above it). */
export const MAX_UPLOAD_BYTES = 8 * 1024 * 1024;

const QUALITIES = [0.85, 0.7, 0.55] as const;
const MAX_SHRINKS = 6;

const HEIC_TYPES = new Set([
  "image/heic",
  "image/heif",
  "image/heic-sequence",
  "image/heif-sequence",
]);

/**
 * False for HEIC/HEIF (most browsers can't decode it, and the API takes only
 * JPEG, PNG and WebP) and for anything that says it isn't an image. A file
 * with no type is let through to the decoder, which has the last word.
 */
export function isSupportedImage(file: File): boolean {
  const type = file.type.toLowerCase();
  if (HEIC_TYPES.has(type)) return false;
  if (/\.(heic|heif)$/i.test(file.name)) return false;
  return type === "" || type.startsWith("image/");
}

function toJpeg(canvas: HTMLCanvasElement, quality: number) {
  return new Promise<Blob | null>((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", quality),
  );
}

/**
 * The photo's size as displayed (EXIF orientation applied), read from the
 * header through an <img>, without decoding the pixels into a bitmap.
 */
function displaySize(file: File): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    const done = () => URL.revokeObjectURL(url);
    img.onload = () => {
      done();
      resolve({ width: img.naturalWidth, height: img.naturalHeight });
    };
    img.onerror = () => {
      done();
      reject(new Error("undecodable"));
    };
    img.src = url;
  });
}

/**
 * Decodes straight to at most `maxSide` on the longest side, so a 48 MP photo
 * never sits in memory at full size. Only the longest side is given: the
 * other follows the aspect ratio, so the picture is never stretched whichever
 * way the browser orders orientation and resizing.
 */
async function decode(file: File, maxSide: number): Promise<ImageBitmap> {
  const { width, height } = await displaySize(file);
  const longest = Math.max(width, height);
  const options: ImageBitmapOptions = { imageOrientation: "from-image" };
  if (longest > maxSide) {
    const scale = maxSide / longest;
    options.resizeQuality = "high";
    if (width >= height) options.resizeWidth = Math.round(width * scale);
    else options.resizeHeight = Math.round(height * scale);
  }
  return createImageBitmap(file, options);
}

/**
 * Re-encodes a label photo in the browser: JPEG, longest side ≤ `maxSide`,
 * at most 8 MB, EXIF orientation applied. Throws ApiError `unsupported_image`
 * for HEIC or a file that can't be decoded (before anything is uploaded),
 * `image_too_large` if it can't be brought under the limit.
 */
export async function resizeImage(file: File, maxSide = 2000): Promise<Blob> {
  if (!isSupportedImage(file)) throw new ApiError("unsupported_image");
  let bitmap: ImageBitmap;
  try {
    bitmap = await decode(file, maxSide);
  } catch {
    throw new ApiError("unsupported_image");
  }
  try {
    const longest = Math.max(bitmap.width, bitmap.height);
    let scale = longest > 0 ? Math.min(1, maxSide / longest) : 1;
    for (let i = 0; i < MAX_SHRINKS; i++) {
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(bitmap.width * scale));
      canvas.height = Math.max(1, Math.round(bitmap.height * scale));
      const ctx = canvas.getContext("2d");
      if (!ctx) throw new ApiError("unsupported_image");
      ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
      for (const q of QUALITIES) {
        const blob = await toJpeg(canvas, q);
        if (blob && blob.type === "image/jpeg" && blob.size <= MAX_UPLOAD_BYTES)
          return blob;
      }
      scale *= 0.75;
    }
    throw new ApiError("image_too_large");
  } finally {
    bitmap.close?.();
  }
}
