import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MyFoods } from "@/features/foods/components/MyFoods";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, json } from "../../support/api-stub";
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
const en = MESSAGES.en;

const food = (id: string, name: string) => ({ id, name });
const recipe = (id: string, name: string, incomplete: string[] = []) => ({
  id,
  name,
  servings: 2,
  incomplete_nutrients: incomplete,
  updated_at: "2026-11-07T00:00:00Z",
});

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("MyFoods", () => {
  it("lists custom foods and recipes", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/custom-foods", {
        items: [food("f1", "Ladoo")],
        next_cursor: null,
      })
      .on("GET", "/v1/recipes", {
        items: [recipe("r1", "Rice and dal", ["fibre_g"])],
        next_cursor: null,
      });
    renderIntl(<MyFoods />);
    expect((await screen.findByTestId("my-food")).textContent).toContain(
      "Ladoo",
    );
    expect(screen.getByTestId("my-food").getAttribute("href")).toBe(
      "/en/diary/foods/f1",
    );
    const r = screen.getByTestId("my-recipe");
    expect(r.getAttribute("href")).toBe("/en/diary/recipes/r1");
    expect(r.textContent).toContain(en.recipes.incomplete);
  });

  it("paginates", async () => {
    const api = apiStub(fetchMock)
      .on("GET", "/v1/recipes", { items: [], next_cursor: null })
      .on("GET", "/v1/custom-foods", (c) =>
        c.query.get("cursor")
          ? json(200, { items: [food("f2", "Chivda")], next_cursor: null })
          : json(200, { items: [food("f1", "Ladoo")], next_cursor: "abc" }),
      );
    renderIntl(<MyFoods />);
    await userEvent.click(await screen.findByTestId("foods-more"));
    await waitFor(() =>
      expect(screen.getAllByTestId("my-food")).toHaveLength(2),
    );
    expect(
      api.callsTo("GET", "/v1/custom-foods").at(-1)?.query.get("cursor"),
    ).toBe("abc");
    expect(screen.queryByTestId("foods-more")).toBeNull();
  });

  it("empty shows the empty state", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/recipes", { items: [], next_cursor: null })
      .on("GET", "/v1/custom-foods", { items: [], next_cursor: null });
    renderIntl(<MyFoods />);
    expect(await screen.findByText(en.recipes.empty)).toBeTruthy();
  });
});
