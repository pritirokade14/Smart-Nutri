import en from "@smartnutri/i18n/messages/en.json";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import HomePage from "@/app/[locale]/(app)/home/page";
import { ApiError } from "@/lib/api/errors";

const fetchMe = vi.hoisted(() => vi.fn());
vi.mock("@/features/me/api/me", () => ({ fetchMe }));

afterEach(cleanup);
beforeEach(() => fetchMe.mockReset());

function view() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={en}>
        <HomePage />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

describe("home", () => {
  it("loading: a status message and skeletons", async () => {
    let resolve: (v: unknown) => void = () => {};
    fetchMe.mockReturnValue(new Promise((r) => (resolve = r)));
    view();
    expect(screen.getByRole("status").textContent).toBe(en.common.loading);
    expect(screen.getAllByTestId("skeleton").length).toBeGreaterThan(0);
    resolve({ display_name: "A", email: null });
    await screen.findByRole("heading", { level: 1 });
  });

  it("error: the mapped message and a retry that refetches", async () => {
    fetchMe.mockRejectedValueOnce(new ApiError("rate_limited", 429));
    fetchMe.mockResolvedValueOnce({ display_name: "Asha", email: null });
    view();
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.rate_limited,
    );
    await userEvent.click(
      screen.getByRole("button", { name: en.common.retry }),
    );
    expect(
      await screen.findByRole("heading", { level: 1, name: "Hello, Asha" }),
    ).toBeTruthy();
  });

  it("data: greeting, the three ways to check a product, and the disclaimer", async () => {
    fetchMe.mockResolvedValue({ display_name: null, email: "a@b.c" });
    view();
    expect(
      await screen.findByRole("heading", { level: 1, name: "Hello, a@b.c" }),
    ).toBeTruthy();
    const hrefs = [
      [en.scan.title, "/en/scan"],
      [en.label.title, "/en/scan/label"],
      [en.label.enter_manually, "/en/scan/manual"],
    ];
    for (const [name, href] of hrefs) {
      expect(
        screen
          .getByRole("link", { name: new RegExp(name as string) })
          .getAttribute("href"),
      ).toBe(href);
    }
    expect(screen.getByText(en.common.disclaimer)).toBeTruthy();
  });
});
