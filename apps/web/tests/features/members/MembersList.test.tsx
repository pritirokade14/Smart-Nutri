import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MembersList } from "@/features/members/components/MembersList";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub } from "../../support/api-stub";

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

const member = (over: Record<string, unknown>) => ({
  id: "a0000000-0000-4000-8000-000000000001",
  name: "",
  relation: "self",
  is_primary: true,
  birth_year: null,
  ...over,
});

function show(members: unknown[]) {
  apiStub(fetchMock).on("GET", "/v1/members", members);
  render(
    <QueryClientProvider client={new QueryClient()}>
      <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
        <MembersList />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("MembersList", () => {
  it("shows an unnamed account holder as You once", async () => {
    show([member({})]);
    const row = await screen.findByTestId("member-row");
    expect(within(row).getAllByText(en.members.you_badge)).toHaveLength(1);
  });

  it("a named account holder keeps the You badge", async () => {
    show([member({ name: "Asha" })]);
    const row = await screen.findByTestId("member-row");
    expect(within(row).getByText("Asha")).toBeTruthy();
    expect(within(row).getAllByText(en.members.you_badge)).toHaveLength(1);
  });
});
