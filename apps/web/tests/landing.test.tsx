import messages from "@smartnutri/i18n/messages/en.json";
import { act, cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { Suspense } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import LandingPage, { generateMetadata } from "@/app/[locale]/(public)/page";

vi.mock("next-intl/server", () => ({
  setRequestLocale: () => {},
  getTranslations: async () => (key: string) =>
    key
      .split(".")
      .reduce<unknown>((o, k) => (o as Record<string, unknown>)[k], messages),
}));

afterEach(cleanup);

async function renderLanding() {
  await act(async () => {
    render(
      <NextIntlClientProvider locale="en" messages={messages}>
        <Suspense>
          <LandingPage params={Promise.resolve({ locale: "en" })} />
        </Suspense>
      </NextIntlClientProvider>,
    );
  });
}

describe("landing", () => {
  it("hero states the value proposition and leads to sign-in", async () => {
    await renderLanding();
    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: messages.landing.hero_title,
      }),
    ).toBeTruthy();
    expect(screen.getByText(messages.landing.hero_body)).toBeTruthy();
    const start = screen.getByRole("link", {
      name: messages.landing.cta_start,
    });
    expect(start.getAttribute("href")).toBe("/en/sign-in");
    const how = screen.getByRole("link", { name: messages.landing.how_title });
    expect(how.getAttribute("href")).toBe("#how");
  });

  it("explains how it works in three ordered steps", async () => {
    await renderLanding();
    const section = await screen.findByRole("region", {
      name: messages.landing.how_title,
    });
    const steps = within(section).getAllByRole("listitem");
    expect(steps).toHaveLength(3);
    const l = messages.landing;
    for (const [i, [title, body]] of [
      [l.step1_title, l.step1_body],
      [l.step2_title, l.step2_body],
      [l.step3_title, l.step3_body],
    ].entries()) {
      expect(
        within(steps[i] as HTMLElement).getByText(title as string),
      ).toBeTruthy();
      expect(
        within(steps[i] as HTMLElement).getByText(body as string),
      ).toBeTruthy();
    }
  });

  it("shows the disclaimer and no member data or status labels", async () => {
    await renderLanding();
    expect(await screen.findByText(messages.common.disclaimer)).toBeTruthy();
    expect(document.body.innerHTML).not.toMatch(/data-verdict|verdict/);
  });

  it("has SEO metadata with canonical and hreflang alternates", async () => {
    const meta = await generateMetadata({
      params: Promise.resolve({ locale: "en" }),
    });
    expect(meta.title).toBe(messages.landing.meta_title);
    expect(meta.description).toBe(messages.landing.meta_description);
    expect(meta.alternates?.canonical).toBe("/en");
    expect(meta.alternates?.languages).toEqual({
      en: "/en",
      hi: "/hi",
      mr: "/mr",
    });
  });
});
