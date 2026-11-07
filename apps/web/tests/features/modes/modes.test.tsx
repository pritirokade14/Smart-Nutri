import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
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
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AppNav } from "@/components/shell/AppNav";
import { ModeSwitcher } from "@/features/modes/components/ModeSwitcher";
import { MoreList } from "@/features/modes/components/MoreMenu";
import {
  DESTINATION_PATH,
  type Destination,
  MODE_TABLE,
  type UserType,
} from "@/features/modes/layouts";
import {
  type UserTypesOut,
  userTypesKey,
} from "@/features/user-types/api/userTypes";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";

// Plan 9 Task 13: the same cases as Android's Task 10, named identically.

const nav = vi.hoisted(() => ({ pathname: "/en/home" }));
vi.mock("next/navigation", () => ({
  usePathname: () => nav.pathname,
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: {
      getSession: async () => ({
        data: { session: { access_token: "token" } },
      }),
    },
  }),
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

type Layouts = {
  priority: string[];
  default_type: string;
  destinations: string[];
  always_first_card_when_any_member_has_allergens: string;
  modes: Record<string, { tabs: string[]; home_cards: string[] }>;
};
const FIXTURE = JSON.parse(
  readFileSync(
    join(process.cwd(), "../../packages/test-fixtures/modes/layouts.json"),
    "utf8",
  ),
) as Layouts;
const MODES = Object.keys(FIXTURE.modes) as UserType[];

const en = MESSAGES.en;
let api: ReturnType<typeof apiStub>;
beforeEach(() => {
  nav.pathname = "/en/home";
  fetchMock.mockReset();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

function wrap(ui: ReactNode, seed?: UserTypesOut) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  if (seed) client.setQueryData(userTypesKey, seed);
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return client;
}

const out = (types: UserType[], active: UserType): UserTypesOut => ({
  types,
  follow_ups: {},
  active_type: active,
  answered: true,
  answered_at: "2026-11-04T00:00:00Z",
  prefill: null,
});

const label = (d: string) => en.nav[d as keyof typeof en.nav];
const href = (d: string) =>
  `/en/${DESTINATION_PATH[d as Destination] ?? "missing"}`;

describe("focused modes (T13)", () => {
  it("layouts match shared fixture", () => {
    expect(MODE_TABLE).toEqual(FIXTURE);
    for (const mode of MODES) {
      const { tabs, home_cards } = FIXTURE.modes[mode] as {
        tabs: string[];
        home_cards: string[];
      };
      expect(tabs).toHaveLength(5);
      expect(tabs[0]).toBe("home");
      expect(tabs[1]).toBe("scan");
      expect(tabs[4]).toBe("profile");
      expect(home_cards.at(-1)).toBe("recent_scans");
    }
  });

  it.each(MODES)(
    "each mode shows its five tabs with scan second (%s)",
    (mode) => {
      for (const variant of ["bar", "rail"] as const) {
        wrap(<AppNav locale="en" variant={variant} mode={mode} />);
        const bar = screen.getByRole("navigation", { name: en.nav.label });
        const tabs = within(bar).getAllByTestId("nav-tab");
        const want = FIXTURE.modes[mode]?.tabs ?? [];
        expect(tabs.map((l) => l.textContent)).toEqual(want.map(label));
        expect(tabs.map((l) => l.getAttribute("href"))).toEqual(want.map(href));
        expect(tabs[1]?.getAttribute("href")).toBe("/en/scan");
        for (const l of tabs) expect(l.querySelector("svg")).toBeTruthy();
        cleanup();
      }
    },
  );

  it.each(MODES)("more lists every destination not in the bar (%s)", (mode) => {
    wrap(<MoreList locale="en" mode={mode} />);
    const tabs = FIXTURE.modes[mode]?.tabs ?? [];
    const want = FIXTURE.destinations.filter((d) => !tabs.includes(d));
    const links = within(screen.getByTestId("more-list")).getAllByRole("link");
    expect(links.map((l) => l.textContent)).toEqual(want.map(label));
    expect(links.map((l) => l.getAttribute("href"))).toEqual(want.map(href));
  });

  it.each(MODES)("every destination reachable in every mode (%s)", (mode) => {
    // The desktop rail shows the bar's tabs, then More: nothing hidden.
    wrap(<AppNav locale="en" variant="rail" mode={mode} />);
    const hrefs = within(screen.getByRole("navigation", { name: en.nav.label }))
      .getAllByRole("link")
      .map((l) => l.getAttribute("href"));
    expect([...hrefs].sort()).toEqual(FIXTURE.destinations.map(href).sort());
    // Each one is a real route.
    const app = join(process.cwd(), "src/app/[locale]");
    for (const d of FIXTURE.destinations) {
      const path = DESTINATION_PATH[d as Destination];
      expect(
        existsSync(join(app, "(app)", path, "page.tsx")) ||
          existsSync(join(app, "(public)", path, "page.tsx")),
      ).toBe(true);
    }
    // Scan (then a result) and the allergy entry (Family -> members).
    expect(hrefs).toContain("/en/scan");
    expect(hrefs).toContain("/en/family");
    expect(existsSync(join(app, "(app)/result/[barcode]/page.tsx"))).toBe(true);
    expect(existsSync(join(app, "(app)/members/[id]/page.tsx"))).toBe(true);
  });

  it.each([
    ["gym", "/en/compare", "scan"], // Compare moved to More: it opens from Scan
    ["eat_better", "/en/compare", "compare"],
    ["health_condition", "/en/compare", "scan"],
    ["allergy_diet", "/en/search", "search"],
    ["family", "/en/search", null],
    ["gym", "/en/result/8901063201089", "scan"],
    ["gym", "/en/protein", "protein"],
    ["family", "/en/members/new", "family"],
    ["gym", "/en/family", null],
    ["gym", "/en/members/new", null],
  ] as const)(
    "active tab in %s for %s prefers the exact tab",
    (mode, path, tab) => {
      nav.pathname = path;
      wrap(<AppNav locale="en" variant="bar" mode={mode} />);
      const current = screen
        .getAllByTestId("nav-tab")
        .filter((l) => l.getAttribute("aria-current") === "page")
        .map((l) => l.textContent);
      expect(current).toEqual(tab ? [label(tab)] : []);
    },
  );

  it("the bar follows the stored active mode, eat_better while loading", async () => {
    let resolve: (r: Response) => void = () => {};
    api.on(
      "GET",
      "/v1/me/user-types",
      () => new Promise<Response>((r) => (resolve = r)),
    );
    wrap(<AppNav locale="en" variant="bar" />);
    const tabs = () =>
      screen.getAllByTestId("nav-tab").map((l) => l.textContent);
    expect(tabs()).toEqual(FIXTURE.modes.eat_better?.tabs.map(label));
    await waitFor(() =>
      expect(api.callsTo("GET", "/v1/me/user-types")).toHaveLength(1),
    );
    resolve(json(200, out(["gym", "family"], "gym")));
    await waitFor(() =>
      expect(tabs()).toEqual(FIXTURE.modes.gym?.tabs.map(label)),
    );
  });

  it("switcher hidden with one type, shown with two, calls set_active", async () => {
    wrap(<ModeSwitcher />, out(["gym"], "gym"));
    expect(screen.queryByRole("radiogroup")).toBeNull();
    cleanup();

    api.on("PATCH", "/v1/me/user-types/active", (c) =>
      json(200, {
        ...out(["gym", "allergy_diet"], "gym"),
        active_type: (c.body as { active_type: UserType }).active_type,
      }),
    );
    wrap(<ModeSwitcher />, out(["gym", "allergy_diet"], "allergy_diet"));
    const group = screen.getByRole("radiogroup", {
      name: en.modes.switcher_label,
    });
    const radios = within(group).getAllByRole("radio");
    // Safety-first priority order.
    expect(radios.map((r) => r.textContent)).toEqual([
      en.modes.name.allergy_diet,
      en.modes.name.gym,
    ]);
    expect(radios[0]?.getAttribute("aria-checked")).toBe("true");
    await userEvent.click(radios[1] as HTMLElement);
    expect(radios[1]?.getAttribute("aria-checked")).toBe("true");
    await waitFor(() =>
      expect(
        api.callsTo("PATCH", "/v1/me/user-types/active").map((c) => c.body),
      ).toEqual([{ active_type: "gym" }]),
    );
  });

  it("switcher rolls back when set_active fails", async () => {
    api.on(
      "PATCH",
      "/v1/me/user-types/active",
      json(500, envelope("internal_error")),
    );
    wrap(<ModeSwitcher />, out(["family", "gym"], "family"));
    const radios = screen.getAllByRole("radio");
    await userEvent.click(radios[1] as HTMLElement);
    await waitFor(() =>
      expect(radios[0]?.getAttribute("aria-checked")).toBe("true"),
    );
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
