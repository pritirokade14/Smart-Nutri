import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CustomFoodForm } from "@/features/foods/components/CustomFoodForm";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { renderIntl } from "../../support/diary-render";

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: { getSession: async () => ({ data: { session: null } }) },
  }),
}));
const push = vi.hoisted(() => vi.fn());
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace: vi.fn(), refresh: vi.fn() }),
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

const en = MESSAGES.en;
const FOOD_ID = "b0000000-0000-4000-8000-000000000001";
const OUT = {
  id: FOOD_ID,
  name: "Homemade ladoo",
  brand: null,
  basis: "g",
  per_100: {},
  entered: {
    values_per: "serving",
    serving_g: 40,
    nutrients: { energy_kcal: 180, protein_g: 3 },
  },
  serving_g: 40,
  density_g_per_ml: null,
  barcode: null,
  portions: [],
  created_at: "2026-11-07T00:00:00Z",
  updated_at: "2026-11-07T00:00:00Z",
};

beforeEach(() => {
  fetchMock.mockReset();
  push.mockReset();
});
afterEach(cleanup);

const body = (api: ReturnType<typeof apiStub>, method = "POST") =>
  api.callsTo(method, "/v1/custom-foods")[0].body as Record<string, unknown>;

describe("CustomFoodForm", () => {
  it("blank sends absent not zero", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/custom-foods", () =>
      json(201, OUT),
    );
    renderIntl(<CustomFoodForm />);
    await userEvent.type(screen.getByLabelText(en.custom_food.name), "Ladoo");
    await userEvent.type(
      screen.getByLabelText(en.confirm.field.energy_kcal),
      "180",
    );
    await userEvent.click(
      screen.getByRole("button", { name: en.custom_food.save }),
    );
    await waitFor(() => expect(push).toHaveBeenCalled());
    const sent = body(api);
    expect(sent.nutrients).toEqual({ energy_kcal: 180 });
    expect(sent).toMatchObject({ basis: "g", values_per: "100" });
    expect(sent).not.toHaveProperty("serving_g");
    expect(sent).not.toHaveProperty("brand");
    // The blank-is-unknown copy is on the form.
    expect(screen.getByText(en.foods.blank_is_unknown)).toBeTruthy();
  });

  it("per serving sends values_per serving", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/custom-foods", () =>
      json(201, OUT),
    );
    renderIntl(<CustomFoodForm />);
    await userEvent.type(screen.getByLabelText(en.custom_food.name), "Ladoo");
    await userEvent.click(screen.getByLabelText(en.foods.values_per.serving));
    await userEvent.type(
      screen.getByLabelText(en.custom_food.serving_size),
      "40",
    );
    await userEvent.type(
      screen.getByLabelText(en.confirm.field.protein_g),
      "3",
    );
    await userEvent.click(
      screen.getByRole("button", { name: en.custom_food.save }),
    );
    await waitFor(() => expect(push).toHaveBeenCalled());
    expect(body(api)).toMatchObject({
      values_per: "serving",
      serving_g: 40,
      nutrients: { protein_g: 3 },
    });
  });

  it("api errors map to messages", async () => {
    apiStub(fetchMock).on("POST", "/v1/custom-foods", () =>
      json(422, envelope("custom_food_nutrients_empty")),
    );
    renderIntl(<CustomFoodForm />);
    await userEvent.type(screen.getByLabelText(en.custom_food.name), "Ladoo");
    await userEvent.click(
      screen.getByRole("button", { name: en.custom_food.save }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.custom_food_nutrients_empty,
    );
    expect(push).not.toHaveBeenCalled();
  });

  it("implausible value marks the field and shows its message", async () => {
    apiStub(fetchMock).on("POST", "/v1/custom-foods", () =>
      json(
        422,
        envelope("implausible_value", { fields: ["body.nutrients.protein_g"] }),
      ),
    );
    renderIntl(<CustomFoodForm />);
    await userEvent.type(screen.getByLabelText(en.custom_food.name), "Ladoo");
    await userEvent.type(
      screen.getByLabelText(en.confirm.field.protein_g),
      "900",
    );
    await userEvent.click(
      screen.getByRole("button", { name: en.custom_food.save }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.implausible_value,
    );
    expect(
      screen
        .getByLabelText(en.confirm.field.protein_g)
        .getAttribute("aria-invalid"),
    ).toBe("true");
  });

  it("barcode already used maps to its message", async () => {
    apiStub(fetchMock).on("POST", "/v1/custom-foods", () =>
      json(409, envelope("barcode_already_used")),
    );
    renderIntl(<CustomFoodForm />);
    await userEvent.type(screen.getByLabelText(en.custom_food.name), "Ladoo");
    await userEvent.click(
      screen.getByRole("button", { name: en.custom_food.save }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.barcode_already_used,
    );
  });

  it("edit loads the typed values and delete shows the history kept note", async () => {
    const api = apiStub(fetchMock)
      .on("GET", "/v1/custom-foods", { items: [OUT], next_cursor: null })
      .on(
        "DELETE",
        `/v1/custom-foods/${FOOD_ID}`,
        new Response(null, { status: 204 }),
      );
    renderIntl(<CustomFoodForm id={FOOD_ID} />);
    expect(
      ((await screen.findByLabelText(en.custom_food.name)) as HTMLInputElement)
        .value,
    ).toBe("Homemade ladoo");
    expect(
      (screen.getByLabelText(en.confirm.field.energy_kcal) as HTMLInputElement)
        .value,
    ).toBe("180");
    // A nutrient that was left blank stays blank.
    expect(
      (screen.getByLabelText(en.confirm.field.fat_g) as HTMLInputElement).value,
    ).toBe("");
    await userEvent.click(
      screen.getByRole("button", { name: en.custom_food.delete }),
    );
    const dialog = await screen.findByTestId("confirm-dialog");
    expect(dialog.textContent).toContain(en.custom_food.history_kept);
    await userEvent.click(
      dialog.querySelectorAll("button")[1] as HTMLButtonElement,
    );
    await waitFor(() =>
      expect(api.callsTo("DELETE", `/v1/custom-foods/${FOOD_ID}`)).toHaveLength(
        1,
      ),
    );
  });
});
