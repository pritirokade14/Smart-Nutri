import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getDiaryAddContext,
  isAddTripPath,
  setDiaryAddContext,
} from "@/features/diary/lib/addContext";

afterEach(() => {
  vi.useRealTimers();
  window.sessionStorage.clear();
});

describe("diary add-food context", () => {
  it("expires after 30 minutes", () => {
    vi.useFakeTimers();
    setDiaryAddContext({ method: "search", slotId: null, localDate: null });
    vi.advanceTimersByTime(29 * 60 * 1000);
    expect(getDiaryAddContext()).not.toBeNull();
    vi.advanceTimersByTime(2 * 60 * 1000);
    expect(getDiaryAddContext()).toBeNull();
    expect(window.sessionStorage.getItem("sn.diaryAddContext")).toBeNull();
  });

  it("a context without a timestamp is ignored", () => {
    window.sessionStorage.setItem(
      "sn.diaryAddContext",
      JSON.stringify({ method: "search", slotId: null, localDate: null }),
    );
    expect(getDiaryAddContext()).toBeNull();
  });

  it("only the add-food pages keep it", () => {
    for (const p of [
      "/en/diary",
      "/en/search",
      "/en/scan/label",
      "/hi/result/123",
      "/mr/product/abc",
    ])
      expect(isAddTripPath(p)).toBe(true);
    for (const p of ["/en/home", "/en/profile", "/en/history", "/en/family"])
      expect(isAddTripPath(p)).toBe(false);
  });
});
