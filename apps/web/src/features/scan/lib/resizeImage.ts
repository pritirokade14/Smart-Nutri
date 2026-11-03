import { ApiError } from "@/lib/api/errors";

/** The API's upload limit (413 image_too_large above it). */
export const MAX_UPLOAD_BYTES = 8 * 1024 * 1024;

const QUALITIES = [0.85, 0.7, 0.55] as const;
const MAX_SHRINKS = 6;

function toJpeg(canvas: HTMLCanvasElement, quality: number) {
  return new Promise<Blob | null>((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", quality),
  );
}

/**
 * Re-encodes a label photo in the browser: JPEG, longest side ≤ `maxSide`,
 * at most 8 MB. EXIF orientation is applied while decoding. Throws ApiError
 * `unsupported_image` if the file can't be decoded, `image_too_large` if it
 * can't be brought under the limit.
 */
export async function resizeImage(file: File, maxSide = 2000): Promise<Blob> {
  let bitmap: ImageBitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
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
