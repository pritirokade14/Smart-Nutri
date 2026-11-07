import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FavouriteStar } from "@/features/favourites/components/FavouriteStar";
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
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));

const en = MESSAGES.en;
const REF = { food_id: "f0000000-0000-4000-8000-000000000002" };

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("FavouriteStar", () => {
  it("star toggles add and delete", async () => {
    const api = apiStub(fetchMock)
      .on("POST", "/v1/favourites", json(201, { id: "fav1" }))
      .on("DELETE", "/v1/favourites/fav1", new Response(null, { status: 204 }));
    renderIntl(
      <FavouriteStar
        foodRef={REF}
        favouriteId={null}
        portion={{ quantity: 2, unit: "roti" }}
      />,
    );
    const star = screen.getByRole("button", { name: en.favourites.add });
    await userEvent.click(star);
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: en.favourites.remove }),
      ).toBeTruthy(),
    );
    expect(api.callsTo("POST", "/v1/favourites")[0].body).toEqual({
      ...REF,
      default_quantity: 2,
      default_unit: "roti",
    });
    await userEvent.click(
      screen.getByRole("button", { name: en.favourites.remove }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: en.favourites.add }),
      ).toBeTruthy(),
    );
    expect(api.callsTo("DELETE", "/v1/favourites/fav1")).toHaveLength(1);
  });

  it("limit error shows message", async () => {
    apiStub(fetchMock).on(
      "POST",
      "/v1/favourites",
      json(422, envelope("favourite_limit")),
    );
    renderIntl(<FavouriteStar foodRef={REF} favouriteId={null} />);
    await userEvent.click(
      screen.getByRole("button", { name: en.favourites.add }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.favourite_limit,
    );
  });

  it("food_retired shows message", async () => {
    apiStub(fetchMock).on(
      "POST",
      "/v1/favourites",
      json(422, envelope("food_retired")),
    );
    renderIntl(<FavouriteStar foodRef={REF} favouriteId={null} />);
    await userEvent.click(
      screen.getByRole("button", { name: en.favourites.add }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.food_retired,
    );
  });
});
