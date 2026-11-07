import { describe, expect, it } from "vitest";
import { xOf } from "@/features/weights/components/WeightChart";

const from = Date.parse("2026-11-01T00:00:00Z");
const span = Date.parse("2026-11-11T00:00:00Z") - from;
const PAD = 12;
const RIGHT = 320 - 12;

describe("xOf", () => {
  it("maps the range ends to the padded edges and the middle to the centre", () => {
    expect(xOf("2026-11-01", from, span)).toBe(PAD);
    expect(xOf("2026-11-11", from, span)).toBe(RIGHT);
    expect(xOf("2026-11-06", from, span)).toBe(160);
  });

  it("clamps dates outside the range to the edges", () => {
    expect(xOf("2026-10-20", from, span)).toBe(PAD);
    expect(xOf("2026-12-01", from, span)).toBe(RIGHT);
  });

  it("centres everything when the range is a single day", () => {
    expect(xOf("2026-11-01", from, 0)).toBe(160);
  });
});
