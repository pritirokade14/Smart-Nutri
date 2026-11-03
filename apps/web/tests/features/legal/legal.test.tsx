import { readFileSync } from "node:fs";
import { join } from "node:path";
import en from "@smartnutri/i18n/messages/en.json";
import hi from "@smartnutri/i18n/messages/hi.json";
import { act, cleanup, render, screen, within } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { Suspense } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import PrivacyPage, {
  generateMetadata as privacyMetadata,
} from "@/app/[locale]/(public)/privacy/page";
import TermsPage from "@/app/[locale]/(public)/terms/page";
import robots from "@/app/robots";
import sitemap from "@/app/sitemap";
import { AppShell } from "@/components/shell/AppShell";
import { SiteFooter } from "@/components/shell/SiteFooter";
import { markdown as privacyMd } from "@/content/legal/privacy";
import { markdown as termsMd } from "@/content/legal/terms";
import { Markdown } from "@/features/legal/components/Markdown";
import {
  CONTENT_DIR,
  DOCS_DIR,
  LEGAL_DOCS,
  legalModule,
} from "../../../scripts/sync-legal";

const MESSAGES = { en, hi } as const;
const lookup = (locale: keyof typeof MESSAGES) => (key: string) =>
  key
    .split(".")
    .reduce<unknown>(
      (o, k) => (o as Record<string, unknown>)[k],
      MESSAGES[locale],
    ) as string;
vi.mock("next-intl/server", () => ({
  setRequestLocale: () => {},
  getTranslations: async ({ locale }: { locale: "en" | "hi" }) => {
    const t = lookup(locale);
    return (key: string, values?: Record<string, string>) =>
      Object.entries(values ?? {}).reduce(
        (s, [k, v]) => s.replace(`{${k}}`, v),
        t(key),
      );
  },
}));
vi.mock("next/navigation", () => ({ usePathname: () => "/en/home" }));

afterEach(cleanup);

async function show(ui: React.ReactNode, locale: "en" | "hi" = "en") {
  await act(async () => {
    render(
      <NextIntlClientProvider locale={locale} messages={MESSAGES[locale]}>
        <Suspense>{ui}</Suspense>
      </NextIntlClientProvider>,
    );
  });
}

describe("legal content", () => {
  it("the shipped copies match docs/launch (run `pnpm sync:legal`)", () => {
    for (const { source, target } of LEGAL_DOCS) {
      const md = readFileSync(join(DOCS_DIR, source), "utf8");
      expect(readFileSync(join(CONTENT_DIR, target), "utf8"), target).toBe(
        legalModule(md, source),
      );
    }
  });

  it("drops the editors' note but keeps the policy text", () => {
    expect(privacyMd).not.toContain("CURRENT_VERSIONS");
    expect(privacyMd).not.toContain("apps/api");
    expect(privacyMd).toContain("information, not medical advice");
    expect(privacyMd).toContain("30 days");
  });

  it("points to Profile (the app's name for the page), never Settings (cleanup c6)", () => {
    expect(privacyMd).not.toContain("Settings →");
    expect(privacyMd).toContain("Profile → Privacy and consent");
    expect(privacyMd).toContain("Profile → Delete account");
    expect(termsMd).not.toContain("Settings →");
    expect(termsMd).toContain("Profile → Delete account");
  });

  it("follows ruling G1: verdicts, scans, meal logs and label reading rest on terms", () => {
    expect(privacyMd).toContain(
      "This covers the core service: verdicts, scans, meal logs and **reading the label photos you take**.",
    );
    expect(privacyMd).not.toContain(
      "[Before launch: confirm both apps strip EXIF",
    );
  });
});

describe("Markdown", () => {
  it("renders headings, lists, tables, bold, code and safe links", async () => {
    await show(
      <Markdown
        source={[
          "# Title",
          "",
          "Intro **bold `terms`** text.",
          "Second line.",
          "",
          "## Part",
          "",
          "- one",
          "- two [Privacy Notice](/privacy)",
          "",
          "| A | B |",
          "|---|---|",
          "| x | **y** |",
          "",
          "[evil](javascript:alert(1)) and [site](https://example.org/x)",
        ].join("\n")}
        localeHref={(p) => `/hi${p}`}
      />,
    );
    expect(
      screen.getByRole("heading", { level: 1, name: "Title" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("heading", { level: 2, name: "Part" }),
    ).toBeTruthy();
    expect(screen.getByText("terms").tagName).toBe("CODE");
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(
      screen.getByRole("link", { name: "Privacy Notice" }).getAttribute("href"),
    ).toBe("/hi/privacy");
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("columnheader")).toHaveLength(2);
    expect(within(table).getByText("y").tagName).toBe("STRONG");
    expect(screen.queryByRole("link", { name: "evil" })).toBeNull();
    expect(screen.getByText(/evil/)).toBeTruthy();
    const ext = screen.getByRole("link", { name: "site" });
    expect(ext.getAttribute("href")).toBe("https://example.org/x");
    expect(ext.getAttribute("rel")).toContain("noopener");
  });
});

describe("privacy and terms pages", () => {
  it("privacy is public, shows the draft notice, version and the policy", async () => {
    await show(<PrivacyPage params={Promise.resolve({ locale: "en" })} />);
    expect(
      await screen.findByRole("heading", { level: 1, name: /Privacy Notice/ }),
    ).toBeTruthy();
    expect(screen.getByText(en.legal.draft_notice)).toBeTruthy();
    expect(screen.getByText("Version 2026-11-01")).toBeTruthy();
    expect(screen.queryByText(en.legal.english_only)).toBeNull();
    expect(screen.getAllByRole("table").length).toBeGreaterThan(0);
  });

  it("in Hindi it says the text is English only, and marks it lang=en", async () => {
    await show(<TermsPage params={Promise.resolve({ locale: "hi" })} />, "hi");
    expect(await screen.findByText(hi.legal.english_only)).toBeTruthy();
    const article = screen.getByRole("article");
    expect(article.getAttribute("lang")).toBe("en");
    expect(
      within(article)
        .getByRole("link", { name: "Privacy Notice" })
        .getAttribute("href"),
    ).toBe("/hi/privacy");
  });

  it("metadata has a localized title and hreflang alternates", async () => {
    const meta = await privacyMetadata({
      params: Promise.resolve({ locale: "hi" }),
    });
    expect(meta.title).toBe(hi.legal.privacy_title);
    // I6: noindex until a lawyer signs the drafts off.
    expect(meta.robots).toEqual({ index: false, follow: true });
    expect(meta.alternates?.languages).toEqual({
      en: "/en/privacy",
      hi: "/hi/privacy",
      mr: "/mr/privacy",
    });
  });
});

describe("footer links on every page", () => {
  const expectLinks = (root: HTMLElement, locale: string) => {
    for (const [name, path] of [
      [en.legal.privacy_title, "privacy"],
      [en.legal.terms_title, "terms"],
      [en.methodology.title, "how-we-score"],
    ]) {
      expect(
        within(root).getByRole("link", { name }).getAttribute("href"),
      ).toBe(`/${locale}/${path}`);
    }
  };

  it("public footer", async () => {
    await show(<SiteFooter locale="en" />);
    expectLinks(screen.getByRole("contentinfo"), "en");
  });

  it("logged-in shell", async () => {
    await show(
      <AppShell locale="en">
        <p>{"page"}</p>
      </AppShell>,
    );
    expectLinks(screen.getByRole("contentinfo"), "en");
  });
});

describe("sitemap", () => {
  it("lists the public pages in every locale with hreflang alternates", () => {
    const urls = sitemap().map((e) => e.url);
    for (const l of ["en", "hi", "mr"])
      for (const p of ["", "/how-we-score"])
        expect(urls).toContain(`http://localhost:3000/${l}${p}`);
    expect(urls.some((u) => /home|profile|sign-in|\/p\//.test(u))).toBe(false);
    const how = sitemap().find(
      (e) => e.url === "http://localhost:3000/en/how-we-score",
    );
    expect(how?.alternates?.languages).toEqual({
      en: "http://localhost:3000/en/how-we-score",
      hi: "http://localhost:3000/hi/how-we-score",
      mr: "http://localhost:3000/mr/how-we-score",
    });
  });

  it("leaves the draft legal pages out until lawyer sign-off (I6)", () => {
    const urls = sitemap().map((e) => e.url);
    expect(urls.some((u) => /\/(privacy|terms)$/.test(u))).toBe(false);
  });
});

describe("robots.txt", () => {
  it("allows the public pages and disallows the app routes", () => {
    const r = robots();
    const rule = Array.isArray(r.rules) ? r.rules[0] : r.rules;
    expect(rule.allow).toEqual(expect.arrayContaining(["/"]));
    const dis = ([] as string[]).concat(rule.disallow ?? []);
    for (const p of ["/api/", "/auth/", "/*/home", "/*/scan", "/*/history"])
      expect(dis).toContain(p);
    expect(r.sitemap).toBe("http://localhost:3000/sitemap.xml");
  });
});
