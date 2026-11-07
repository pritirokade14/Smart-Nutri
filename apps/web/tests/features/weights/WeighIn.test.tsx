import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { WeighInDialog } from "@/features/weights/components/WeighInDialog";
import { WeightList } from "@/features/weights/components/WeightList";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { renderIntl } from "../../support/diary-render";

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

const en = MESSAGES.en;
const ROW = (date: string, kg: number | null) => ({
  date,
  weight_kg: kg,
  measured_at: `${date}T00:00:00Z`,
  source: "manual",
  client_id: null,
  numbers_hidden: kg === null,
});

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("WeighInDialog", () => {
  it("needs confirm then save anyway", async () => {
    const api = apiStub(fetchMock).on("PUT", "/v1/weights/2026-11-07", (c) =>
      (c.body as { confirm_unusual: boolean }).confirm_unusual
        ? json(200, ROW("2026-11-07", 70))
        : json(
            422,
            envelope("weight_needs_confirm", {
              previous: 80,
              previous_date: "2026-11-01",
            }),
          ),
    );
    const onClose = vi.fn();
    renderIntl(<WeighInDialog today="2026-11-07" onClose={onClose} />);
    await userEvent.type(screen.getByLabelText(en.weight.title), "70");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    expect((await screen.findByTestId("weight-confirm")).textContent).toBe(
      en.weight.confirm_unusual.replace("{previous}", "80"),
    );
    await userEvent.click(
      screen.getByRole("button", { name: en.weight.save_anyway }),
    );
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const puts = api.callsTo("PUT", "/v1/weights/2026-11-07");
    expect(
      puts.map((c) => (c.body as { confirm_unusual: boolean }).confirm_unusual),
    ).toEqual([false, true]);
    expect((puts[1].body as { weight_kg: number }).weight_kg).toBe(70);
  });

  it("hidden previous shows the hidden copy with no digits", async () => {
    apiStub(fetchMock).on("PUT", "/v1/weights/2026-11-07", () =>
      json(
        422,
        envelope("weight_needs_confirm", {
          previous: null,
          previous_date: null,
        }),
      ),
    );
    renderIntl(<WeighInDialog today="2026-11-07" onClose={vi.fn()} />);
    await userEvent.type(screen.getByLabelText(en.weight.title), "70");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    const el = await screen.findByTestId("weight-confirm");
    expect(el.textContent).toBe(en.weight.confirm_unusual_hidden);
    expect(el.textContent).not.toMatch(/\d/);
  });

  it("editing the value after a confirm asks again from scratch", async () => {
    apiStub(fetchMock).on("PUT", "/v1/weights/2026-11-07", () =>
      json(422, envelope("weight_needs_confirm", { previous: 80 })),
    );
    renderIntl(<WeighInDialog today="2026-11-07" onClose={vi.fn()} />);
    await userEvent.type(screen.getByLabelText(en.weight.title), "70");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    await screen.findByTestId("weight-confirm");
    await userEvent.type(screen.getByLabelText(en.weight.title), "1");
    expect(screen.queryByTestId("weight-confirm")).toBeNull();
    expect(screen.queryByTestId("weight-save-anyway")).toBeNull();
  });

  it("maps weight_out_of_range", async () => {
    apiStub(fetchMock).on("PUT", "/v1/weights/2026-11-07", () =>
      json(422, envelope("weight_out_of_range", { min: 2, max: 300 })),
    );
    renderIntl(<WeighInDialog today="2026-11-07" onClose={vi.fn()} />);
    await userEvent.type(screen.getByLabelText(en.weight.title), "500");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    expect((await screen.findByTestId("weight-error")).textContent).toBe(
      en.error.weight_out_of_range,
    );
  });

  it("a blank or non-numeric weight is not sent", async () => {
    const api = apiStub(fetchMock);
    renderIntl(<WeighInDialog today="2026-11-07" onClose={vi.fn()} />);
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    expect((await screen.findByTestId("weight-error")).textContent).toBe(
      en.error.weight_out_of_range,
    );
    expect(api.calls).toHaveLength(0);
  });

  it("defaults the date to today and shows the same-time tip", () => {
    apiStub(fetchMock);
    renderIntl(<WeighInDialog today="2026-11-07" onClose={vi.fn()} />);
    expect(
      (screen.getByLabelText(en.weight.date) as HTMLInputElement).value,
    ).toBe("2026-11-07");
    expect(screen.getByText(en.weight.tip_same_time)).toBeTruthy();
  });
});

describe("WeightList", () => {
  it("lists newest first, edits and deletes", async () => {
    const api = apiStub(fetchMock)
      .on("GET", "/v1/weights", {
        numbers_hidden: false,
        items: [ROW("2026-11-01", 80), ROW("2026-11-05", 79.4)],
      })
      .on("PUT", "/v1/weights/2026-11-05", ROW("2026-11-05", 79))
      .on(
        "DELETE",
        "/v1/weights/2026-11-01",
        new Response(null, { status: 204 }),
      );
    renderIntl(<WeightList today="2026-11-07" />);
    const rows = await screen.findAllByTestId("weight-row");
    expect(rows.map((r) => r.getAttribute("data-date"))).toEqual([
      "2026-11-05",
      "2026-11-01",
    ]);
    expect(rows[0].textContent).toContain("79.4 kg");

    await userEvent.click(screen.getAllByTestId("weight-edit")[0]);
    const kg = screen.getByLabelText(en.weight.title) as HTMLInputElement;
    expect(kg.value).toBe("79.4");
    await userEvent.clear(kg);
    await userEvent.type(kg, "79");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    await waitFor(() =>
      expect(api.callsTo("PUT", "/v1/weights/2026-11-05")).toHaveLength(1),
    );

    await userEvent.click(screen.getAllByTestId("weight-delete")[1]);
    expect(screen.getByText(en.weight.delete_confirm)).toBeTruthy();
    await userEvent.click(
      screen.getByTestId("confirm-dialog").querySelectorAll("button")[1],
    );
    await waitFor(() =>
      expect(api.callsTo("DELETE", "/v1/weights/2026-11-01")).toHaveLength(1),
    );
  });

  it("maps weight_not_found on delete", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/weights", {
        numbers_hidden: false,
        items: [ROW("2026-11-01", 80)],
      })
      .on("DELETE", "/v1/weights/2026-11-01", () =>
        json(404, envelope("weight_not_found")),
      );
    renderIntl(<WeightList today="2026-11-07" />);
    await userEvent.click(await screen.findByTestId("weight-delete"));
    await userEvent.click(
      screen.getByTestId("confirm-dialog").querySelectorAll("button")[1],
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.weight_not_found,
    );
  });

  it("hidden rows show the date only", async () => {
    apiStub(fetchMock).on("GET", "/v1/weights", {
      numbers_hidden: true,
      items: [ROW("2026-11-01", null)],
    });
    renderIntl(<WeightList today="2026-11-07" />);
    await screen.findByTestId("weight-row");
    expect(screen.queryByTestId("weight-row-kg")).toBeNull();
  });

  it("the four weight error codes have copy in every locale", () => {
    for (const loc of ["en", "hi", "mr"] as const) {
      for (const code of [
        "weight_out_of_range",
        "weight_needs_confirm",
        "weight_not_found",
        "date_range_too_long",
      ]) {
        expect(
          (MESSAGES[loc].error as Record<string, string>)[code],
        ).toBeTruthy();
      }
    }
  });
});
