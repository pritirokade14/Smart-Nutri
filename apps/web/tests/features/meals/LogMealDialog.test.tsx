import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  LogMealDialog,
  type LogMealProduct,
} from "@/features/meals/components/LogMealDialog";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";

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

const DAD = "b0000000-0000-4000-8000-000000000001";
const ME = "a0000000-0000-4000-8000-000000000001";
const MEMBERS = [
  { id: ME, name: "", isPrimary: true },
  { id: DAD, name: "Dad", isPrimary: false },
];
const OFF_BISCUIT: LogMealProduct = {
  productId: null,
  barcode: "8901063201089",
  name: "Sugar Free Biscuit",
  servingSizeG: 25,
};

const mealOut = (over: object = {}) => ({
  id: "c0000000-0000-4000-8000-000000000001",
  member_id: DAD,
  product_id: null,
  barcode: "8901063201089",
  product_name: "Sugar Free Biscuit",
  grade: "D",
  grams: 25,
  eaten_at: "2026-11-03T08:00:00+00:00",
  nutrients: {
    energy_kcal: 120,
    sugars_g: null,
    salt_g: 0.2,
    protein_g: 2,
    fat_g: 5,
    sat_fat_g: 2,
    carbs_g: 17,
  },
  client_id: "x",
  attribution: "attribution.off",
  ...over,
});

const onClose = vi.fn();

function view(
  product: LogMealProduct = OFF_BISCUIT,
  memberId = DAD,
  localDate?: string,
) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider
        locale="en"
        messages={clientMessages(MESSAGES.en)}
      >
        <LogMealDialog
          product={product}
          members={MEMBERS}
          memberId={memberId}
          localDate={localDate}
          onClose={onClose}
        />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

const en = MESSAGES.en;

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
  onClose.mockReset();
});
afterEach(cleanup);

describe("LogMealDialog", () => {
  it("shows online-only notice", () => {
    apiStub(fetchMock);
    view();
    expect(screen.getByText(en.meals.online_only)).toBeTruthy();
    expect(
      screen.getByRole("dialog", { name: en.meals.log.title }),
    ).toBeTruthy();
  });

  it("retry reuses client_id", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals", (_c, n) =>
      n === 1 ? json(500, envelope("internal_error")) : json(201, mealOut()),
    );
    view();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    expect(await screen.findByText(en.error.internal_error)).toBeTruthy();
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    expect(
      await screen.findByText(en.meals.log.saved.replace("{who}", "Dad")),
    ).toBeTruthy();

    const posts = api.callsTo("POST", "/v1/meals");
    expect(posts).toHaveLength(2);
    const [a, b] = posts.map((c) => c.body as Record<string, unknown>);
    expect(typeof a.client_id).toBe("string");
    expect(a.client_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
    expect(b.client_id).toBe(a.client_id);
    expect(a).toEqual(b);
    expect(a).toMatchObject({
      member_id: DAD,
      barcode: "8901063201089",
      servings: 1,
    });
    expect(a).not.toHaveProperty("product_id");
    expect(a).not.toHaveProperty("grams");
  });

  it("a network failure is retried with the same client_id too", async () => {
    let n = 0;
    const api = apiStub(fetchMock);
    const routed = fetchMock.getMockImplementation();
    fetchMock.mockImplementation(async (req: Request) => {
      if (req.method === "POST" && new URL(req.url).pathname === "/v1/meals") {
        n += 1;
        if (n === 1) {
          await routed?.(req); // record the call
          throw new TypeError("Failed to fetch");
        }
      }
      return routed?.(req);
    });
    api.on("POST", "/v1/meals", json(200, mealOut()));
    view();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    expect(await screen.findByText(en.error.network)).toBeTruthy();
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    await screen.findByText(en.meals.log.saved.replace("{who}", "Dad"));
    const ids = api
      .callsTo("POST", "/v1/meals")
      .map((c) => (c.body as { client_id: string }).client_id);
    expect(ids).toHaveLength(2);
    expect(ids[1]).toBe(ids[0]);
  });

  it("servings hidden without serving size: grams only", async () => {
    const api = apiStub(fetchMock).on(
      "POST",
      "/v1/meals",
      json(201, mealOut({ grams: 40 })),
    );
    view({ ...OFF_BISCUIT, servingSizeG: null });
    expect(screen.queryByLabelText(en.meals.log.amount_servings)).toBeNull();
    expect(
      screen.queryByRole("radio", { name: en.meals.log.servings }),
    ).toBeNull();
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(en.meals.log.amount_grams), "40");
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    await screen.findByText(en.meals.log.saved.replace("{who}", "Dad"));
    expect(api.callsTo("POST", "/v1/meals")[0].body).toMatchObject({
      grams: 40,
    });
  });

  it("our own product is logged by product_id, never with a barcode too", async () => {
    const id = "d0000000-0000-4000-8000-000000000009";
    const api = apiStub(fetchMock).on(
      "POST",
      "/v1/meals",
      json(201, mealOut({ product_id: id, barcode: null })),
    );
    view({ ...OFF_BISCUIT, productId: id });
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    await screen.findByText(en.meals.log.saved.replace("{who}", "Dad"));
    const body = api.callsTo("POST", "/v1/meals")[0].body;
    expect(body).toMatchObject({ product_id: id });
    expect(body).not.toHaveProperty("barcode");
  });

  it("switching to grams sends grams; an invalid amount never reaches the API", async () => {
    const api = apiStub(fetchMock).on(
      "POST",
      "/v1/meals",
      json(201, mealOut()),
    );
    view();
    const user = userEvent.setup();
    await user.click(screen.getByRole("radio", { name: en.meals.log.grams }));
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    expect(
      await screen.findByText(
        en.meals.log.amount_invalid.replace("{max}", "5000"),
      ),
    ).toBeTruthy();
    expect(api.callsTo("POST", "/v1/meals")).toHaveLength(0);
    await user.type(screen.getByLabelText(en.meals.log.amount_grams), "6000");
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    expect(api.callsTo("POST", "/v1/meals")).toHaveLength(0);
    await user.clear(screen.getByLabelText(en.meals.log.amount_grams));
    await user.type(screen.getByLabelText(en.meals.log.amount_grams), "30");
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    await screen.findByText(en.meals.log.saved.replace("{who}", "Dad"));
    expect(api.callsTo("POST", "/v1/meals")[0].body).toMatchObject({
      grams: 30,
    });
  });

  it("logs for the member chosen in the picker; the holder reads 'you'", async () => {
    const api = apiStub(fetchMock).on(
      "POST",
      "/v1/meals",
      json(201, mealOut({ member_id: ME })),
    );
    view();
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText(en.meals.log.member), ME);
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    expect(await screen.findByText(en.meals.log.saved_you)).toBeTruthy();
    expect(api.callsTo("POST", "/v1/meals")[0].body).toMatchObject({
      member_id: ME,
    });
    expect(track).toHaveBeenCalledWith("meal_logged");
    // Event name only: no product, member or amount.
    expect(track.mock.calls.every((c) => c.length === 1)).toBe(true);
  });

  it("maps API error codes to i18n text", async () => {
    apiStub(fetchMock).on(
      "POST",
      "/v1/meals",
      json(422, envelope("serving_size_unknown")),
    );
    view();
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: en.meals.log.save }));
    expect(await screen.findByText(en.error.serving_size_unknown)).toBeTruthy();
  });

  it("undo deletes the stored log", async () => {
    const api = apiStub(fetchMock)
      .on("POST", "/v1/meals", json(201, mealOut()))
      .on(
        "DELETE",
        "/v1/meals/c0000000-0000-4000-8000-000000000001",
        new Response(null, { status: 204 }),
      );
    view();
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    await user.click(
      await screen.findByRole("button", { name: en.meals.log.undo }),
    );
    expect(await screen.findByText(en.meals.log.undone)).toBeTruthy();
    expect(
      api.callsTo("DELETE", "/v1/meals/c0000000-0000-4000-8000-000000000001"),
    ).toHaveLength(1);
    expect(track).toHaveBeenCalledWith("meal_log_undone");
  });

  it("shows the stored amount and when it was logged in the success state", async () => {
    apiStub(fetchMock).on("POST", "/v1/meals", json(201, mealOut()));
    view();
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: en.meals.log.save }));
    expect(
      await screen.findByText(en.history.item_amount.replace("{grams}", "25")),
    ).toBeTruthy();
  });

  it("a past time is sent as a timezone-aware datetime", async () => {
    const api = apiStub(fetchMock).on(
      "POST",
      "/v1/meals",
      json(201, mealOut()),
    );
    view();
    const user = userEvent.setup();
    fireEvent.change(screen.getByLabelText(en.meals.log.eaten_at), {
      target: { value: "2026-11-03T09:30" },
    });
    await user.click(screen.getByRole("button", { name: en.meals.log.save }));
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
    );
    const body = api.callsTo("POST", "/v1/meals")[0].body as {
      eaten_at: string;
    };
    expect(body.eaten_at).toMatch(/Z$|[+-]\d{2}:\d{2}$/);
    expect(new Date(body.eaten_at).getTime()).toBe(
      new Date("2026-11-03T09:30").getTime(),
    );
  });

  describe("diary slot and day", () => {
    const SLOTS = ["breakfast", "lunch", "snack", "dinner"].map((k, i) => ({
      id: `d0000000-0000-4000-8000-00000000000${i + 1}`,
      member_id: ME,
      position: i,
      label_key: `diary.slot.${k}`,
      custom_label: null,
      default_time_window: null,
      is_default: true,
      archived: false,
    }));
    const slotsRoute = { items: SLOTS, suggested_slot_id: SLOTS[1].id };

    it("slot chips preselect the server's suggestion and the log sends it", async () => {
      const api = apiStub(fetchMock)
        .on("GET", "/v1/meal-slots", slotsRoute)
        .on("POST", "/v1/meals", (_c) => json(201, mealOut()));
      view();
      const lunch = await screen.findByRole("button", {
        name: en.diary.slot.lunch,
      });
      expect(lunch.getAttribute("aria-pressed")).toBe("true");
      await userEvent.click(
        screen.getByRole("button", { name: en.diary.slot.dinner }),
      );
      await userEvent.click(
        screen.getByRole("button", { name: en.meals.log.save }),
      );
      await waitFor(() =>
        expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
      );
      expect(
        (api.callsTo("POST", "/v1/meals")[0].body as { meal_slot_id: string })
          .meal_slot_id,
      ).toBe(SLOTS[3].id);
    });

    it("no slot list: no chips and no slot sent", async () => {
      const api = apiStub(fetchMock).on("POST", "/v1/meals", (_c) =>
        json(201, mealOut()),
      );
      view();
      await userEvent.click(
        screen.getByRole("button", { name: en.meals.log.save }),
      );
      await waitFor(() =>
        expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
      );
      expect(screen.queryByTestId("slot-chips")).toBeNull();
      expect(api.callsTo("POST", "/v1/meals")[0].body).not.toHaveProperty(
        "meal_slot_id",
      );
    });

    it("a diary day sends local_date and never eaten_at", async () => {
      const api = apiStub(fetchMock).on("POST", "/v1/meals", (_c) =>
        json(201, mealOut()),
      );
      view(OFF_BISCUIT, DAD, "2026-11-05");
      expect(screen.queryByLabelText(en.meals.log.eaten_at)).toBeNull();
      await userEvent.click(
        screen.getByRole("button", { name: en.meals.log.save }),
      );
      await waitFor(() =>
        expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
      );
      const sent = api.callsTo("POST", "/v1/meals")[0].body as Record<
        string,
        unknown
      >;
      expect(sent.local_date).toBe("2026-11-05");
      expect(sent).not.toHaveProperty("eaten_at");
    });
  });
});
