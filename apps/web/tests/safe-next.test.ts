import { describe, expect, it } from "vitest";
import { safeNext } from "@/lib/auth/safe-next";

describe("safeNext", () => {
  it("keeps same-origin relative paths", () => {
    expect(safeNext("/en/home", "/x")).toBe("/en/home");
    expect(safeNext("/en/product/1?a=b", "/x")).toBe("/en/product/1?a=b");
  });

  it.each([
    "//evil.example",
    "https://evil.example",
    "http://evil.example/en/home",
    "/\\evil.example",
    "\\\\evil.example",
    "/%2Fevil.example",
    "/%5Cevil.example",
    "%2F%2Fevil.example",
    "/\t/evil.example",
    "javascript:alert(1)",
    "en/home",
    "",
    null,
    undefined,
  ])("rejects %s", (bad) => {
    expect(safeNext(bad as string | null | undefined, "/en/home")).toBe(
      "/en/home",
    );
  });
});
