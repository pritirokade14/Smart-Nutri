import messages from "@smartnutri/i18n/messages/en.json";
import { act, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { Suspense } from "react";
import { describe, expect, it, vi } from "vitest";
import LandingPage from "@/app/[locale]/(public)/page";

vi.mock("next-intl/server", () => ({ setRequestLocale: () => {} }));
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));

describe("landing", () => {
  it("shows app name and disclaimer", async () => {
    await act(async () => {
      render(
        <NextIntlClientProvider locale="en" messages={messages}>
          <Suspense>
            <LandingPage params={Promise.resolve({ locale: "en" })} />
          </Suspense>
        </NextIntlClientProvider>,
      );
    });
    expect(
      await screen.findByRole("heading", { name: messages.app.name }),
    ).toBeTruthy();
    expect(screen.getByText(messages.common.disclaimer)).toBeTruthy();
  });
});
