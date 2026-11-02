import { describe, expect, it } from "vitest";
import { normalizeBarcode } from "@/features/scan/lib/barcode";

describe("normalizeBarcode", () => {
  it("strips spaces", () =>
    expect(normalizeBarcode(" 8901 0632 0108 9 ")).toBe("8901063201089"));
  it("strips hyphens", () =>
    expect(normalizeBarcode("8901-0632-0108-9")).toBe("8901063201089"));
  it("keeps UPC leading zero", () =>
    expect(normalizeBarcode("012345678905")).toBe("012345678905"));
  it("accepts 8 and 14 digits", () => {
    expect(normalizeBarcode("12345670")).toBe("12345670");
    expect(normalizeBarcode("00012345678905")).toBe("00012345678905");
  });
  it("rejects non-digits", () => expect(normalizeBarcode("abc123")).toBeNull());
  it("rejects 7 and 15 digits", () => {
    expect(normalizeBarcode("1234567")).toBeNull();
    expect(normalizeBarcode("123456789012345")).toBeNull();
  });
  it("rejects empty", () => expect(normalizeBarcode("  ")).toBeNull());
});
