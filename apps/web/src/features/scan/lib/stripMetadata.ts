import { ApiError } from "@/lib/api/errors";

// Label photos are stored for up to 30 days, and phone cameras write the
// location (EXIF GPS) into them. Browsers' canvas encoders write no EXIF, but
// that is not a guarantee, so every upload is cleaned here: walk the JPEG's
// marker segments up to the image data and keep only what decoding needs.
//
// Kept: APP0 (JFIF), APP2 only when it is an ICC colour profile, and every
// non-APP segment (tables, frame, scan). Dropped: APP1 (EXIF, XMP), APP2
// FlashPix, APP3–APP15 (IPTC, Photoshop, maker data) and COM (comments).

const SOI = 0xd8;
const SOS = 0xda;
const APP0 = 0xe0;
const APP2 = 0xe2;
const APP15 = 0xef;
const COM = 0xfe;
const ICC = [..."ICC_PROFILE\0"].map((c) => c.charCodeAt(0));

function unsupported(): never {
  throw new ApiError("unsupported_image");
}

function startsWith(bytes: Uint8Array, at: number, prefix: number[]): boolean {
  return prefix.every((b, i) => bytes[at + i] === b);
}

function keep(marker: number, bytes: Uint8Array, payload: number): boolean {
  if (marker === COM) return false;
  if (marker < APP0 || marker > APP15) return true;
  if (marker === APP0) return true;
  return marker === APP2 && startsWith(bytes, payload, ICC);
}

/** A blob's bytes (FileReader where Blob#arrayBuffer is missing). */
export async function readBytes(blob: Blob): Promise<Uint8Array> {
  if (typeof blob.arrayBuffer === "function")
    return new Uint8Array(await blob.arrayBuffer());
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(new Uint8Array(reader.result as ArrayBuffer));
    reader.onerror = () => reject(reader.error);
    reader.readAsArrayBuffer(blob);
  });
}

/** The index just past the first EOI (0xFFD9) at or after `from`. */
function endOfImage(bytes: Uint8Array, from: number): number {
  for (let i = from; i + 1 < bytes.length; i++) {
    if (bytes[i] === 0xff && bytes[i + 1] === 0xd9) return i + 2;
  }
  return unsupported(); // truncated: no end of image
}

/**
 * The same JPEG without metadata segments. Throws ApiError
 * `unsupported_image` for anything it can't parse, so an uncleaned photo is
 * never uploaded.
 */
export async function stripJpegMetadata(jpeg: Blob): Promise<Blob> {
  const bytes = await readBytes(jpeg);
  if (bytes[0] !== 0xff || bytes[1] !== SOI) unsupported();
  const out: Uint8Array[] = [bytes.subarray(0, 2)];
  let i = 2;
  while (i < bytes.length) {
    if (bytes[i] !== 0xff) unsupported();
    // Any number of 0xFF fill bytes may precede a marker.
    while (bytes[i] === 0xff) i++;
    const marker = bytes[i];
    if (marker === undefined || marker === 0) unsupported();
    const lenAt = i + 1;
    if (lenAt + 1 >= bytes.length) unsupported();
    const length = ((bytes[lenAt] ?? 0) << 8) | (bytes[lenAt + 1] ?? 0);
    const end = lenAt + length;
    if (length < 2 || end > bytes.length) unsupported();
    if (marker === SOS) {
      // Start of scan: image data up to the end-of-image marker. 0xFFD9
      // can't occur inside entropy-coded data (a data 0xFF is stuffed as
      // 0xFF00), so the first one ends the image; anything after it (some
      // cameras append a metadata trailer) is dropped.
      const eoi = endOfImage(bytes, lenAt);
      out.push(new Uint8Array([0xff, marker]), bytes.subarray(lenAt, eoi));
      return new Blob(out as BlobPart[], { type: "image/jpeg" });
    }
    if (keep(marker, bytes, lenAt + 2))
      out.push(new Uint8Array([0xff, marker]), bytes.subarray(lenAt, end));
    i = end;
  }
  unsupported(); // no image data
}
