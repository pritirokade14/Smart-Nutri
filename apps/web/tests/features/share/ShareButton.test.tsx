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
import { ResultShare } from "@/features/share/ResultShare";
import { ShareButton } from "@/features/share/ShareButton";
import { WeeklyShare } from "@/features/share/WeeklyShare";
import { clientMessages, resultMessages } from "@/i18n/client-messages";
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
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));

const en = MESSAGES.en;
const TEXT =
  "Oats — Nutri-Score A (calculated by SmartNutri). Checked with SmartNutri: http://localhost:3000/en";

function intl(ui: React.ReactNode, messages = clientMessages(en)) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider locale="en" messages={messages}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

const nav = navigator as unknown as { share?: unknown };
beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
  Object.defineProperty(navigator, "share", {
    value: undefined,
    configurable: true,
    writable: true,
  });
});
afterEach(cleanup);

describe("ShareButton", () => {
  it("without the Web Share API: preview, privacy note, copy link and WhatsApp", async () => {
    intl(
      <ShareButton
        label={en.share.button}
        text={TEXT}
        url="http://localhost:3000/en"
        event="share_result"
      />,
    );
    const user = userEvent.setup();
    // userEvent installs its own clipboard: watch that one.
    const copy = vi.spyOn(navigator.clipboard, "writeText");
    await user.click(screen.getByRole("button", { name: en.share.button }));
    const dialog = screen.getByRole("dialog", { name: en.share.button });
    expect(within(dialog).getByTestId("share-preview").textContent).toBe(TEXT);
    expect(within(dialog).getByText(en.share.privacy_note)).toBeTruthy();
    const wa = within(dialog).getByRole("link", { name: en.share.whatsapp });
    expect(wa.getAttribute("href")).toBe(
      `https://wa.me/?text=${encodeURIComponent(TEXT)}`,
    );
    expect(wa.getAttribute("rel")).toContain("noopener");
    await user.click(
      within(dialog).getByRole("button", { name: en.share.copy_link }),
    );
    expect(copy).toHaveBeenCalledWith("http://localhost:3000/en");
    expect(await within(dialog).findByText(en.share.copied)).toBeTruthy();
    expect(track).toHaveBeenCalledWith("share_result");
    expect(track.mock.calls.every((c) => c.length === 1)).toBe(true);
  });

  it("with the Web Share API: shares the text and offers no fallback", async () => {
    const share = vi.fn(async () => {});
    nav.share = share;
    intl(
      <ShareButton
        label={en.share.button}
        text={TEXT}
        url="http://localhost:3000/en"
        event="share_result"
      />,
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: en.share.button }));
    const dialog = screen.getByRole("dialog");
    expect(
      within(dialog).queryByRole("link", { name: en.share.whatsapp }),
    ).toBeNull();
    await user.click(
      within(dialog).getByRole("button", { name: en.share.button }),
    );
    expect(share).toHaveBeenCalledWith({ text: TEXT });
    await waitFor(() => expect(track).toHaveBeenCalledWith("share_result"));
  });

  it("a cancelled native share is not an error", async () => {
    nav.share = vi.fn(async () => {
      throw new DOMException("cancelled", "AbortError");
    });
    intl(
      <ShareButton
        label={en.share.button}
        text={TEXT}
        url="u"
        event="share_result"
      />,
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: en.share.button }));
    await user.click(
      within(screen.getByRole("dialog")).getByRole("button", {
        name: en.share.button,
      }),
    );
    expect(screen.queryByRole("alert")).toBeNull();
    expect(track).not.toHaveBeenCalled();
  });
});

describe("ResultShare", () => {
  const verdicts = [
    { member_name: "Ravi Patil", relation: "parent", status: "avoid" },
    { member_name: "", relation: "self", status: "caution" },
  ];

  it("defaults to product and grade only; members are opt-in (ruling SH1)", async () => {
    intl(
      <ResultShare
        productName="Sugar Free Biscuit"
        grade="D"
        barcode="8901063201089"
        verdicts={verdicts}
      />,
      resultMessages(en),
    );
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: en.share.button }));
    const preview = () => screen.getByTestId("share-preview").textContent;
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(boxes).toHaveLength(2);
    expect(boxes.every((b) => !b.checked)).toBe(true);
    expect(preview()).toBe(
      "Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri). Checked with SmartNutri: http://localhost:3000/en/p/8901063201089",
    );
    expect(screen.getByText(en.share.include)).toBeTruthy();
    await user.click(screen.getByRole("checkbox", { name: "Me: Caution" }));
    expect(preview()).toBe(
      "Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri). Me: Caution. Checked with SmartNutri: http://localhost:3000/en/p/8901063201089",
    );
    await user.click(screen.getByRole("checkbox", { name: "Ravi: Avoid" }));
    expect(preview()).toBe(
      "Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri). Ravi: Avoid, Me: Caution. Checked with SmartNutri: http://localhost:3000/en/p/8901063201089",
    );
    await user.click(screen.getByRole("checkbox", { name: "Ravi: Avoid" }));
    expect(preview()).toBe(
      "Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri). Me: Caution. Checked with SmartNutri: http://localhost:3000/en/p/8901063201089",
    );
  });

  it("without NEXT_PUBLIC_SITE_URL: no link in the text and no Copy link", async () => {
    vi.stubEnv("NEXT_PUBLIC_SITE_URL", "");
    try {
      intl(
        <ResultShare
          productName="Sugar Free Biscuit"
          grade="D"
          barcode="8901063201089"
          verdicts={verdicts}
        />,
        resultMessages(en),
      );
      const user = userEvent.setup();
      await user.click(screen.getByRole("button", { name: en.share.button }));
      const dialog = screen.getByRole("dialog");
      expect(within(dialog).getByTestId("share-preview").textContent).toBe(
        "Sugar Free Biscuit — Nutri-Score D (calculated by SmartNutri).",
      );
      expect(
        within(dialog).queryByRole("button", { name: en.share.copy_link }),
      ).toBeNull();
      expect(
        within(dialog).getByRole("link", { name: en.share.whatsapp }),
      ).toBeTruthy();
    } finally {
      vi.unstubAllEnvs();
    }
  });

  it("a product without a barcode links to the site root", async () => {
    intl(
      <ResultShare
        productName="Khakhra"
        grade={null}
        barcode={null}
        verdicts={[]}
      />,
      resultMessages(en),
    );
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: en.share.button }));
    expect(screen.getByTestId("share-preview").textContent).toBe(
      "Khakhra — not enough label data for a Nutri-Score. Checked with SmartNutri: http://localhost:3000/en",
    );
  });
});

describe("WeeklyShare", () => {
  it("counts only, from week_counts", async () => {
    const api = apiStub(fetchMock).on("GET", "/v1/meals/week_counts", {
      start: "2026-10-28",
      end: "2026-11-03",
      scans: 12,
      logged: 10,
    });
    intl(<WeeklyShare today="2026-11-03" />);
    const user = userEvent.setup();
    await user.click(
      await screen.findByRole("button", { name: en.share.weekly_button }),
    );
    expect(screen.getByTestId("share-preview").textContent).toBe(
      "Our week on SmartNutri — products checked: 12, items logged: 10. Checked with SmartNutri: http://localhost:3000/en",
    );
    expect(screen.getByText(en.share.privacy_note)).toBeTruthy();
    expect(
      api.callsTo("GET", "/v1/meals/week_counts")[0].query.get("date"),
    ).toBe("2026-11-03");
  });
});
