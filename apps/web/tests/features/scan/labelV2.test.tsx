import messages from "@smartnutri/i18n/messages/en.json";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DraftForm } from "@/features/scan/components/DraftForm";
import { LabelUpload } from "@/features/scan/components/LabelUpload";
import { WarningBanner } from "@/features/scan/components/WarningBanner";
import {
  highlightedFields,
  imageQualityReasons,
} from "@/features/scan/lib/warnings";
import { draftFile, envelope, json, SCAN_ID } from "../../support/drafts";

// Label accuracy v2 follow-ups on web: the new confirm warnings, and a
// retake hint per reason on image_quality_low (details.reasons).

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: {
      getSession: async () => ({
        data: { session: { access_token: "tok" } },
      }),
    },
  }),
}));
vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));
vi.mock("@/features/scan/lib/resizeImage", () => ({
  resizeImage: async () =>
    new Blob([new Uint8Array(10)], { type: "image/jpeg" }),
  MAX_UPLOAD_BYTES: 8 * 1024 * 1024,
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

afterEach(cleanup);

const intl = (ui: React.ReactNode) =>
  render(
    <QueryClientProvider client={new QueryClient()}>
      <NextIntlClientProvider locale="en" messages={messages}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );

describe("label v2 confirm warnings", () => {
  it.each([
    ["fat_parts_mismatch", messages.warning.fat_parts_mismatch],
    ["decimal_shift:per_100g.fat_g", messages.warning.decimal_shift],
    ["column_mismatch:sugars_g", messages.warning.column_mismatch],
  ])("%s shows its own message, never a verdict colour", (w, text) => {
    intl(<WarningBanner warning={w} />);
    const banner = screen.getByTestId(`warning-${w}`);
    expect(within(banner).getByText(text)).toBeTruthy();
    expect(banner.className).not.toMatch(/verdict-ok/);
  });

  it("highlights the fields each warning names", () => {
    expect([...highlightedFields(["fat_parts_mismatch"])].sort()).toEqual([
      "fat_g",
      "sat_fat_g",
    ]);
    expect([...highlightedFields(["decimal_shift:per_100g.fat_g"])]).toEqual([
      "fat_g",
    ]);
    expect([...highlightedFields(["column_mismatch:sugars_g"])]).toEqual([
      "sugars_g",
    ]);
  });

  it.each([
    ["column_mismatch.json", "sugars_g", messages.warning.column_mismatch],
    ["energy_decimal_shift.json", "fat_g", messages.warning.decimal_shift],
  ])(
    "%s: the banner and the highlighted row on the confirm form",
    (file, field, text) => {
      const draft = draftFile(file);
      intl(<DraftForm scan={{ scanId: SCAN_ID, draft }} onSave={vi.fn()} />);
      expect(screen.getByText(text)).toBeTruthy();
      const rows = screen.getAllByTestId(`row-${field}`);
      expect(
        rows.some((r) => r.className.includes("border-verdict-caution")),
      ).toBe(true);
    },
  );
});

describe("image_quality_low retake hints", () => {
  it("keeps only known reasons, in a fixed order", () => {
    expect(
      imageQualityReasons({ reasons: ["too_small", "x", "blur"] }),
    ).toEqual(["blur", "too_small"]);
    expect(imageQualityReasons({})).toEqual([]);
    expect(imageQualityReasons(null)).toEqual([]);
  });

  async function upload(details: object) {
    fetchMock.mockImplementation(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const req =
          input instanceof Request ? input : new Request(String(input), init);
        const path = new URL(req.url).pathname;
        if (path === "/v1/scans/upload-url")
          return json(200, {
            upload_url:
              "http://127.0.0.1:54321/storage/v1/object/upload/sign/labels/a/x.jpg?token=t",
            path: "a/x.jpg",
            expires_in: 120,
          });
        if (req.method === "PUT") return new Response("{}", { status: 200 });
        return json(422, envelope("image_quality_low", details));
      },
    );
    intl(<LabelUpload barcode={null} />);
    await userEvent.upload(
      screen.getByLabelText(messages.label.take_photo),
      new File([new Uint8Array(20)], "l.jpg", { type: "image/jpeg" }),
    );
    return screen.findByTestId("retake-hints");
  }

  it("one hint per reason, with the retake title and actions", async () => {
    const hints = await upload({ reasons: ["blur", "glare"] });
    expect(
      within(hints)
        .getAllByRole("listitem")
        .map((l) => l.textContent),
    ).toEqual([messages.image_quality.blur, messages.image_quality.glare]);
    expect(screen.getByRole("alert").textContent).toBe(
      messages.image_quality.title,
    );
    expect(
      screen.getByRole("button", { name: messages.label.retake }),
    ).toBeTruthy();
    expect(
      screen.getByRole("link", { name: messages.label.enter_manually }),
    ).toBeTruthy();
  });

  it("no known reason: the generic hint", async () => {
    const hints = await upload({ reasons: ["something_new"] });
    expect(
      within(hints).getByText(messages.image_quality.hint_generic),
    ).toBeTruthy();
  });
});
