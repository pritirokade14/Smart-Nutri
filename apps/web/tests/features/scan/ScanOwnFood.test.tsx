import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ScanPage from "@/app/[locale]/(app)/scan/page";
import { apiStub, envelope, json } from "../../support/api-stub";
import { renderIntl } from "../../support/diary-render";
import { dalDetail } from "../../support/foods-fixtures";

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
const push = vi.hoisted(() => vi.fn());
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace: vi.fn() }),
}));
vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));
vi.mock("@/features/scan/components/BarcodeScanner", () => ({
  BarcodeScanner: () => null,
}));

const CODE = "8901234567890";

beforeEach(() => {
  fetchMock.mockReset();
  push.mockReset();
});
afterEach(cleanup);

async function submit() {
  renderIntl(<ScanPage />);
  await userEvent.type(screen.getByRole("textbox"), CODE);
  await userEvent.click(screen.getByRole("button"));
}

describe("scan page own-food lookup", () => {
  it("own custom food goes to the portion picker", async () => {
    const own = {
      ...dalDetail(),
      kind: "custom_food",
      id: "cf1",
      name: "Ladoo",
    };
    apiStub(fetchMock)
      .on("GET", `/v1/foods/barcode/${CODE}`, own)
      .on("GET", "/v1/foods/custom_food/cf1", own);
    await submit();
    await screen.findByTestId("portion-picker");
    expect(push).not.toHaveBeenCalled();
  });

  it("a product keeps the verdict flow", async () => {
    apiStub(fetchMock).on("GET", `/v1/foods/barcode/${CODE}`, {
      ...dalDetail(),
      kind: "off",
      id: CODE,
    });
    await submit();
    await waitFor(() =>
      expect(push).toHaveBeenCalledWith(`/en/result/${CODE}`),
    );
  });

  it("a failed lookup keeps the verdict flow", async () => {
    apiStub(fetchMock).on(
      "GET",
      `/v1/foods/barcode/${CODE}`,
      json(404, envelope("not_found")),
    );
    await submit();
    await waitFor(() =>
      expect(push).toHaveBeenCalledWith(`/en/result/${CODE}`),
    );
  });
});
