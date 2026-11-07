import en from "@smartnutri/i18n/messages/en.json";
import hi from "@smartnutri/i18n/messages/hi.json";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { Suspense } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import FamilyPage from "@/app/[locale]/(app)/family/page";
import HistoryPage from "@/app/[locale]/(app)/history/page";
import ProfilePage from "@/app/[locale]/(app)/profile/page";
import { AppNav } from "@/components/shell/AppNav";
import { LanguageSwitcher } from "@/components/shell/LanguageSwitcher";

const path = vi.hoisted(() => ({ value: "/en/home" }));
vi.mock("next/navigation", () => ({
  usePathname: () => path.value,
  useRouter: () => ({ replace: vi.fn(), push: vi.fn(), refresh: vi.fn() }),
}));
vi.mock("next-intl/server", () => ({ setRequestLocale: () => {} }));
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({ auth: { signOut: vi.fn() } }),
}));

afterEach(cleanup);

const intl = (ui: React.ReactNode, locale = "en", messages = en) =>
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider locale={locale} messages={messages}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );

// The health-condition mode's bar (layouts.json); every mode's bar is
// covered in tests/features/modes.
const MODE = "health_condition" as const;
const TABS = [
  ["home", "/en/home"],
  ["scan", "/en/scan"],
  ["diary", "/en/history"],
  ["family", "/en/family"],
  ["profile", "/en/profile"],
] as const;

describe("AppNav", () => {
  it.each(["bar", "rail"] as const)(
    "%s: five tabs in order, each with an icon and a label",
    (variant) => {
      path.value = "/en/home";
      intl(<AppNav locale="en" variant={variant} mode={MODE} />);
      const nav = screen.getByRole("navigation", { name: en.nav.label });
      const links = within(nav).getAllByTestId("nav-tab");
      expect(links.map((l) => l.textContent)).toEqual(
        TABS.map(([k]) => en.nav[k]),
      );
      expect(links.map((l) => l.getAttribute("href"))).toEqual(
        TABS.map(([, h]) => h),
      );
      for (const l of links) expect(l.querySelector("svg")).toBeTruthy();
    },
  );

  it.each([
    ["/en/home", "home"],
    ["/en/scan", "scan"],
    ["/en/scan/label", "scan"],
    ["/en/result/8901063201089", "scan"],
    ["/en/product/7d1d2f8a-1111-4c3b-9a0e-0123456789ab", "scan"],
    ["/en/history", "diary"],
    ["/en/family", "family"],
    ["/en/members/new", "family"],
    ["/en/members/7d1d2f8a-1111-4c3b-9a0e-0123456789ab", "family"],
    ["/en/profile", "profile"],
  ] as const)("%s marks %s as the current tab", (p, tab) => {
    path.value = p;
    intl(<AppNav locale="en" variant="bar" mode={MODE} />);
    const current = screen
      .getAllByRole("link")
      .filter((l) => l.getAttribute("aria-current") === "page");
    expect(current.map((l) => l.textContent)).toEqual([en.nav[tab]]);
  });

  it("uses the active locale in links and labels", () => {
    path.value = "/hi/home";
    intl(<AppNav locale="hi" variant="bar" mode={MODE} />, "hi", hi);
    expect(
      screen.getByRole("link", { name: hi.nav.family }).getAttribute("href"),
    ).toBe("/hi/family");
  });
});

describe("LanguageSwitcher", () => {
  it("links the current page in each language, marking the active one", () => {
    path.value = "/en/scan/label";
    intl(<LanguageSwitcher locale="en" />);
    const group = screen.getByRole("navigation", { name: en.language.label });
    const links = within(group).getAllByRole("link");
    expect(links.map((l) => [l.textContent, l.getAttribute("href")])).toEqual([
      [en.language.en, "/en/scan/label"],
      [en.language.hi, "/hi/scan/label"],
      [en.language.mr, "/mr/scan/label"],
    ]);
    expect(links.map((l) => l.getAttribute("hreflang"))).toEqual([
      "en",
      "hi",
      "mr",
    ]);
    expect(
      links.filter((l) => l.getAttribute("aria-current") === "true"),
    ).toHaveLength(1);
    expect(links[0]?.getAttribute("aria-current")).toBe("true");
  });

  it("the locale root maps to the other locale roots", () => {
    path.value = "/hi";
    intl(<LanguageSwitcher locale="hi" />, "hi", hi);
    expect(
      screen.getByRole("link", { name: hi.language.mr }).getAttribute("href"),
    ).toBe("/mr");
  });
});

describe("app pages", () => {
  // History, family and profile are real pages now; they load from the API.
  const withQuery = (ui: React.ReactNode) =>
    intl(
      <QueryClientProvider
        client={
          new QueryClient({ defaultOptions: { queries: { retry: false } } })
        }
      >
        {ui}
      </QueryClientProvider>,
    );

  it("family: the members title and the list loading", async () => {
    await act(async () => {
      withQuery(
        <Suspense>
          <FamilyPage params={Promise.resolve({ locale: "en" })} />
        </Suspense>,
      );
    });
    expect(
      await screen.findByRole("heading", { level: 1, name: en.members.title }),
    ).toBeTruthy();
    expect(screen.queryByText(en.common.coming_soon)).toBeNull();
  });

  it("history: the title, no coming-soon state, and the disclaimer", async () => {
    await act(async () => {
      withQuery(
        <Suspense>
          <HistoryPage params={Promise.resolve({ locale: "en" })} />
        </Suspense>,
      );
    });
    expect(
      await screen.findByRole("heading", { level: 1, name: en.history.title }),
    ).toBeTruthy();
    expect(screen.queryByText(en.common.coming_soon)).toBeNull();
    expect(screen.getByTestId("disclaimer")).toBeTruthy();
  });

  it("profile: privacy and consent, and sign out", async () => {
    await act(async () => {
      withQuery(
        <Suspense>
          <ProfilePage params={Promise.resolve({ locale: "en" })} />
        </Suspense>,
      );
    });
    expect(
      await screen.findByRole("heading", { level: 1, name: en.profile.title }),
    ).toBeTruthy();
    expect(
      screen.getByRole("heading", { level: 2, name: en.profile.privacy_title }),
    ).toBeTruthy();
    expect(
      await screen.findByRole("button", { name: en.auth.signOut }),
    ).toBeTruthy();
  });
});
