import { cleanup, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DiaryView } from "@/features/diary/components/DiaryView";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { diaryDay } from "../../support/diary-fixtures";
import { renderIntl } from "../../support/diary-render";
import { weightTrend } from "../../support/weight-fixtures";

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: { getSession: async () => ({ data: { session: null } }) },
  }),
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});
vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));

beforeEach(() => {
  fetchMock.mockReset();
  apiStub(fetchMock)
    .on("GET", "/v1/diary/day", () => json(200, diaryDay("day_complete_under")))
    .on(
      "GET",
      "/v1/targets/settings",
      json(404, envelope("goal_settings_not_found")),
    )
    .on("GET", "/v1/meal-slots", { items: [], suggested_slot_id: "x" })
    .on("GET", "/v1/weights/trend", () =>
      json(200, weightTrend("weekly_rate_loss")),
    )
    .on("GET", "/v1/weights", { items: [], numbers_hidden: false })
    .on("GET", "/v1/targets", () =>
      json(200, {
        flags: [],
        numbers_hidden: { energy: false, macros: false },
      }),
    );
});
afterEach(cleanup);

describe("Diary Progress tab", () => {
  it("the third view opens Progress", async () => {
    renderIntl(<DiaryView />);
    await userEvent.click(
      await screen.findByRole("button", {
        name: MESSAGES.en.diary.view.progress,
      }),
    );
    expect(await screen.findByTestId("progress-view")).toBeTruthy();
  });

  it("?view=progress opens Progress directly", async () => {
    renderIntl(<DiaryView view="progress" />);
    expect(await screen.findByTestId("progress-view")).toBeTruthy();
  });
});
