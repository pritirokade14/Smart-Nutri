// @vitest-environment node
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  redirect: (to: string) => {
    throw new Error(`REDIRECT:${to}`);
  },
}));

import HistoryPage from "@/app/[locale]/(app)/history/page";

describe("/history", () => {
  it.each(["en", "hi", "mr"])(
    "redirects to the diary in %s",
    async (locale) => {
      await expect(
        HistoryPage({ params: Promise.resolve({ locale }) }),
      ).rejects.toThrow(`REDIRECT:/${locale}/diary`);
    },
  );
});
