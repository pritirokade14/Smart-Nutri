import { describe, expect, it } from "vitest";
import {
  readBytes,
  stripJpegMetadata,
} from "@/features/scan/lib/stripMetadata";

const ascii = (s: string) => [...s].map((c) => c.charCodeAt(0));

/** One marker segment: FF <type> <len hi> <len lo> <payload>. */
function segment(type: number, payload: number[]): number[] {
  const len = payload.length + 2;
  return [0xff, type, len >> 8, len & 0xff, ...payload];
}

// A JPEG as a phone camera writes it: JFIF, EXIF with a GPS block, an ICC
// profile, FlashPix and Photoshop/IPTC blocks, a comment, then image data.
const GPS = [...ascii("GPS"), 0x12, 0x34, ...ascii("N 18.52 E 73.85")];
const PARTS = {
  soi: [0xff, 0xd8],
  jfif: segment(0xe0, [...ascii("JFIF"), 0, 1, 1, 0, 0, 1, 0, 1, 0, 0]),
  exif: segment(0xe1, [...ascii("Exif"), 0, 0, ...ascii("MM"), ...GPS]),
  xmp: segment(0xe1, ascii("http://ns.adobe.com/xap/1.0/\0<x:gps/>")),
  icc: segment(0xe2, [...ascii("ICC_PROFILE"), 0, 1, 1, 9, 9, 9]),
  fpxr: segment(0xe2, [...ascii("FPXR"), 0, 7, 7]),
  iptc: segment(0xed, [...ascii("Photoshop 3.0"), 0, ...ascii("Pune")]),
  comment: segment(0xfe, ascii("shot at home")),
  dqt: segment(0xdb, [0, ...new Array(64).fill(1)]),
  sos: segment(0xda, [1, 1, 0, 0, 0x3f, 0]),
  // Entropy-coded data, with a stuffed 0xFF00 and a restart marker.
  scan: [0x12, 0xff, 0x00, 0x34, 0xff, 0xd0, 0x56],
  eoi: [0xff, 0xd9],
};

function jpeg(...parts: (keyof typeof PARTS)[]): Blob {
  return new Blob([new Uint8Array(parts.flatMap((p) => PARTS[p]))], {
    type: "image/jpeg",
  });
}

const bytes = async (b: Blob) => [...(await readBytes(b))];
const text = async (b: Blob) => String.fromCharCode(...(await readBytes(b)));

describe("stripJpegMetadata", () => {
  it("removes EXIF (with GPS), XMP, FlashPix, IPTC and comments", async () => {
    const out = await stripJpegMetadata(
      jpeg(
        "soi",
        "jfif",
        "exif",
        "xmp",
        "icc",
        "fpxr",
        "iptc",
        "comment",
        "dqt",
        "sos",
        "scan",
        "eoi",
      ),
    );
    const s = await text(out);
    for (const gone of [
      "Exif",
      "GPS",
      "N 18.52",
      "xap",
      "FPXR",
      "Photoshop",
      "Pune",
      "shot at home",
    ])
      expect(s, gone).not.toContain(gone);
    expect(out.type).toBe("image/jpeg");
    expect(await bytes(out)).toEqual([
      ...PARTS.soi,
      ...PARTS.jfif,
      ...PARTS.icc,
      ...PARTS.dqt,
      ...PARTS.sos,
      ...PARTS.scan,
      ...PARTS.eoi,
    ]);
  });

  it("leaves a clean JPEG byte for byte", async () => {
    const clean = jpeg("soi", "jfif", "dqt", "sos", "scan", "eoi");
    expect(await bytes(await stripJpegMetadata(clean))).toEqual(
      await bytes(clean),
    );
  });

  it("skips fill bytes between markers", async () => {
    const out = await stripJpegMetadata(
      new Blob([
        new Uint8Array([
          ...PARTS.soi,
          0xff,
          ...PARTS.exif,
          ...PARTS.dqt,
          ...PARTS.sos,
          ...PARTS.scan,
          ...PARTS.eoi,
        ]),
      ]),
    );
    expect(await text(out)).not.toContain("Exif");
  });

  it("drops a trailer appended after the end of the image", async () => {
    const out = await stripJpegMetadata(
      new Blob([
        new Uint8Array([
          ...PARTS.soi,
          ...PARTS.dqt,
          ...PARTS.sos,
          ...PARTS.scan,
          ...PARTS.eoi,
          ...ascii("SEFT GPS 18.52"),
        ]),
      ]),
    );
    expect(await text(out)).not.toContain("GPS");
    expect((await bytes(out)).slice(-2)).toEqual(PARTS.eoi);
  });

  it.each([
    ["not a JPEG", new Uint8Array([0x89, 0x50, 0x4e, 0x47])],
    [
      "a truncated segment",
      new Uint8Array([0xff, 0xd8, 0xff, 0xe1, 0x40, 0x00, 1, 2]),
    ],
    ["no image data", new Uint8Array([...PARTS.soi, ...PARTS.exif])],
    [
      "image data with no end",
      new Uint8Array([...PARTS.soi, ...PARTS.sos, ...PARTS.scan]),
    ],
  ])("refuses %s (never uploads what it could not clean)", async (_, data) => {
    await expect(stripJpegMetadata(new Blob([data]))).rejects.toMatchObject({
      code: "unsupported_image",
    });
  });
});
