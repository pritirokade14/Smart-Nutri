import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CopyDialog } from "@/features/diary/components/CopyDialog";
import { DiaryView } from "@/features/diary/components/DiaryView";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { diaryDay } from "../../support/diary-fixtures";
import { digitsOutsideAllowed, renderIntl } from "../../support/diary-render";

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
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));

const en = MESSAGES.en;
const posted = (api: ReturnType<typeof apiStub>) =>
  api
    .callsTo("POST", "/v1/meals/copy")
    .map((c) => c.body as Record<string, string>);
const meals = (n: number) =>
  Array.from({ length: n }, (_, i) => ({ id: `m${i}` }));

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

function open(target: Parameters<typeof CopyDialog>[0]["target"]) {
  const onCopied = vi.fn();
  const onClose = vi.fn();
  renderIntl(
    <CopyDialog
      target={target}
      today="2026-11-07"
      onClose={onClose}
      onCopied={onCopied}
    />,
  );
  return { onCopied, onClose };
}
const submit = () =>
  userEvent.click(
    screen.getByRole("button", { name: en.diary.copy_yesterday }),
  );

describe("CopyDialog", () => {
  it("copy yesterday sends a whole-day copy", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals/copy", (_c) =>
      json(201, { created: meals(2) }),
    );
    const { onCopied, onClose } = open({
      kind: "yesterday",
      toDate: "2026-11-07",
    });
    await submit();
    await waitFor(() => expect(onCopied).toHaveBeenCalledWith(2));
    expect(onClose).toHaveBeenCalled();
    const [body] = posted(api);
    expect(body).toMatchObject({
      from_date: "2026-11-06",
      to_date: "2026-11-07",
    });
    expect(body).not.toHaveProperty("from_slot_id");
    expect(body).not.toHaveProperty("to_slot_id");
    expect(track.mock.calls).toEqual([
      ["diary_entry_added", { method: "copy" }],
    ]);
  });

  it("copy yesterday into a past day copies the day before it", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals/copy", (_c) =>
      json(201, { created: meals(1) }),
    );
    open({ kind: "yesterday", toDate: "2026-11-05" });
    await submit();
    await waitFor(() => expect(posted(api)).toHaveLength(1));
    expect(posted(api)[0]).toMatchObject({
      from_date: "2026-11-04",
      to_date: "2026-11-05",
    });
  });

  it("retry reuses client_id", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals/copy", (_c, n) =>
      n === 1
        ? json(503, envelope("internal_error"))
        : json(200, { created: meals(1) }),
    );
    const { onCopied } = open({ kind: "yesterday", toDate: "2026-11-07" });
    await submit();
    await screen.findByRole("alert");
    await submit();
    await waitFor(() => expect(onCopied).toHaveBeenCalledWith(1));
    expect(posted(api)[1].client_id).toBe(posted(api)[0].client_id);
  });

  it.each([
    ["copy_source_empty", 422],
    ["date_too_old", 422],
    ["copy_too_many", 422],
  ])("copy errors map to messages (%s)", async (code, status) => {
    apiStub(fetchMock).on(
      "POST",
      "/v1/meals/copy",
      json(status, envelope(code)),
    );
    open({ kind: "yesterday", toDate: "2026-11-07" });
    await submit();
    expect((await screen.findByRole("alert")).textContent).toBe(
      (en.error as Record<string, string>)[code],
    );
  });

  it("offline copy shows the online-only note", async () => {
    fetchMock.mockRejectedValue(new TypeError("offline"));
    open({ kind: "yesterday", toDate: "2026-11-07" });
    await submit();
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.meals.online_only,
    );
  });

  it("copy a day sends the picked day into the shown day", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals/copy", (_c) =>
      json(201, { created: meals(1) }),
    );
    open({ kind: "day", toDate: "2026-11-07" });
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.copy_day }),
    );
    await waitFor(() => expect(posted(api)).toHaveLength(1));
    expect(posted(api)[0]).toMatchObject({
      from_date: "2026-11-06",
      to_date: "2026-11-07",
    });
  });

  it("copy a meal sends its slot and the picked target", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals/copy", (_c) =>
      json(201, { created: meals(1) }),
    );
    open({ kind: "meal", fromDate: "2026-11-06", fromSlotId: "slot-b" });
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.copy_meal }),
    );
    await waitFor(() => expect(posted(api)).toHaveLength(1));
    expect(posted(api)[0]).toMatchObject({
      from_date: "2026-11-06",
      from_slot_id: "slot-b",
      to_date: "2026-11-07",
    });
  });
});

describe("copy toast", () => {
  it("the copied toast uses Latin digits in Marathi", async () => {
    const day = diaryDay("day_hide_all");
    const copied = day.slots.flatMap((s) => s.entries).slice(0, 3);
    apiStub(fetchMock)
      .on("GET", "/v1/diary/day", day)
      .on(
        "GET",
        "/v1/targets/settings",
        json(404, envelope("goal_settings_not_found")),
      )
      .on("GET", "/v1/meal-slots", { items: [], suggested_slot_id: "x" })
      .on("POST", "/v1/meals/copy", json(201, { created: copied }));
    renderIntl(<DiaryView />, "mr");
    await userEvent.click(
      await screen.findByRole("button", { name: MESSAGES.mr.nav.more }),
    );
    await userEvent.click(
      screen.getByRole("menuitem", { name: MESSAGES.mr.diary.copy_yesterday }),
    );
    await userEvent.click(
      screen
        .getByTestId("copy-dialog")
        .querySelector('button[type="submit"]') as HTMLElement,
    );
    const toast = await screen.findByTestId("diary-notice");
    expect(toast.textContent).toContain("3");
    expect(toast.textContent).not.toMatch(/[०-९]/);
  });

  it("copied toast shows count only under hide_all", async () => {
    const day = diaryDay("day_hide_all");
    const copied = day.slots.flatMap((s) => s.entries).slice(0, 3);
    const api = apiStub(fetchMock)
      .on("GET", "/v1/diary/day", day)
      .on(
        "GET",
        "/v1/targets/settings",
        json(404, envelope("goal_settings_not_found")),
      )
      .on("GET", "/v1/meal-slots", { items: [], suggested_slot_id: "x" })
      .on("POST", "/v1/meals/copy", json(201, { created: copied }));
    renderIntl(<DiaryView />);
    await userEvent.click(
      await screen.findByRole("button", { name: en.nav.more }),
    );
    await userEvent.click(
      screen.getByRole("menuitem", { name: en.diary.copy_yesterday }),
    );
    await userEvent.click(
      screen
        .getByTestId("copy-dialog")
        .querySelector('button[type="submit"]') as HTMLElement,
    );
    const toast = await screen.findByTestId("diary-notice");
    expect(toast.textContent).toBe("3 items copied");
    expect(api.callsTo("POST", "/v1/meals/copy")).toHaveLength(1);
    // Nothing else on the day shows a digit for a hidden value.
    expect(digitsOutsideAllowed().join("")).toBe("3");
  });
});
