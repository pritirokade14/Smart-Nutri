import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DeleteAccount } from "@/features/account/components/DeleteAccount";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";

const signOut = vi.hoisted(() => vi.fn(async () => ({ error: null })));
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: {
      getSession: async () => ({
        data: { session: { access_token: "token" } },
      }),
      signOut,
    },
  }),
}));
const analytics = vi.hoisted(() => ({
  track: vi.fn(),
  resetAnalytics: vi.fn(),
}));
vi.mock("@/lib/analytics", () => analytics);
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

const en = MESSAGES.en;
let api: ReturnType<typeof apiStub>;
let assign: ReturnType<typeof vi.fn>;
beforeEach(() => {
  fetchMock.mockReset();
  signOut.mockClear();
  analytics.track.mockClear();
  analytics.resetAnalytics.mockClear();
  api = apiStub(fetchMock);
  assign = vi.fn();
  vi.stubGlobal("location", { ...window.location, assign });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  client.setQueryData(["members"], [{ id: "m1", name: "Dad" }]);
  client.setQueryData(["analyze", "8901063201089", "en"], { verdicts: [] });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
        <DeleteAccount retryDelayMs={0} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return client;
}

async function openDialog() {
  await userEvent.click(
    screen.getByRole("button", { name: en.settings.delete_button }),
  );
  return screen.getByRole("dialog");
}

const confirmLabel = en.settings.delete_confirm_label.replace(
  "{word}",
  en.settings.delete_confirm_word,
);

describe("DeleteAccount", () => {
  it("explains what is deleted", () => {
    setup();
    expect(
      screen.getByRole("heading", { name: en.settings.delete_title }),
    ).toBeTruthy();
    expect(screen.getByText(en.settings.delete_body)).toBeTruthy();
  });

  it("delete_requires_typed_confirmation", async () => {
    api.on("DELETE", "/v1/me", json(204));
    setup();
    const dialog = await openDialog();
    const confirm = within(dialog).getByRole("button", {
      name: en.settings.delete_confirm,
    }) as HTMLButtonElement;
    expect(confirm.disabled).toBe(true);
    const input = within(dialog).getByLabelText(confirmLabel);
    await userEvent.type(input, "delet");
    expect(confirm.disabled).toBe(true);
    await userEvent.click(confirm);
    expect(api.callsTo("DELETE", "/v1/me")).toHaveLength(0);
    await userEvent.type(input, "e");
    expect(confirm.disabled).toBe(false);
  });

  it("cancel closes without calling the API", async () => {
    setup();
    const dialog = await openDialog();
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.common.cancel }),
    );
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(api.calls).toHaveLength(0);
  });

  it("delete_success_signs_out, clears every cache and shows goodbye", async () => {
    api.on("DELETE", "/v1/me", json(204));
    const client = setup();
    const dialog = await openDialog();
    await userEvent.type(
      within(dialog).getByLabelText(confirmLabel),
      en.settings.delete_confirm_word,
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.settings.delete_confirm }),
    );
    await waitFor(() => expect(assign).toHaveBeenCalledWith("/en/goodbye"));
    expect(api.callsTo("DELETE", "/v1/me")).toHaveLength(1);
    expect(signOut).toHaveBeenCalledWith({ scope: "local" });
    expect(client.getQueryCache().getAll()).toHaveLength(0);
    expect(analytics.track).toHaveBeenCalledWith("account_deleted");
    expect(analytics.resetAnalytics).toHaveBeenCalled();
  });

  it("retries a 503 deletion_incomplete by itself", async () => {
    api.on("DELETE", "/v1/me", (_c, n) =>
      n < 3 ? json(503, envelope("deletion_incomplete")) : json(204),
    );
    setup();
    const dialog = await openDialog();
    await userEvent.type(within(dialog).getByLabelText(confirmLabel), "DELETE");
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.settings.delete_confirm }),
    );
    await waitFor(() => expect(assign).toHaveBeenCalledWith("/en/goodbye"));
    expect(api.callsTo("DELETE", "/v1/me")).toHaveLength(3);
  });

  it("delete_503_shows_retry when retries run out, and Try again finishes it", async () => {
    let fail = true;
    api.on("DELETE", "/v1/me", () =>
      fail ? json(503, envelope("deletion_incomplete")) : json(204),
    );
    setup();
    const dialog = await openDialog();
    await userEvent.type(within(dialog).getByLabelText(confirmLabel), "DELETE");
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.settings.delete_confirm }),
    );
    expect(
      await within(dialog).findByText(en.error.deletion_incomplete),
    ).toBeTruthy();
    expect(signOut).not.toHaveBeenCalled();
    expect(assign).not.toHaveBeenCalled();
    fail = false;
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.common.retry }),
    );
    await waitFor(() => expect(assign).toHaveBeenCalledWith("/en/goodbye"));
  });

  it("a 4xx is not retried and shows its message", async () => {
    api.on("DELETE", "/v1/me", json(429, envelope("rate_limited")));
    setup();
    const dialog = await openDialog();
    await userEvent.type(within(dialog).getByLabelText(confirmLabel), "DELETE");
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.settings.delete_confirm }),
    );
    expect(await within(dialog).findByText(en.error.rate_limited)).toBeTruthy();
    expect(api.callsTo("DELETE", "/v1/me")).toHaveLength(1);
  });
});
