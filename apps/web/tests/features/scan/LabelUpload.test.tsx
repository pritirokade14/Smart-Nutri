import messages from "@smartnutri/i18n/messages/en.json";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getScanDraft } from "@/features/scan/api/draftCache";
import { LabelUpload } from "@/features/scan/components/LabelUpload";
import { ApiError } from "@/lib/api/errors";
import { envelope, json, scanDraft } from "../../support/drafts";

const router = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => router }));
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: {
      getSession: async () => ({
        data: { session: { access_token: "tok" } },
      }),
    },
  }),
}));
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));
const resize = vi.hoisted(() => vi.fn());
vi.mock("@/features/scan/lib/resizeImage", () => ({
  resizeImage: resize,
  MAX_UPLOAD_BYTES: 8 * 1024 * 1024,
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

const SIGNED =
  "http://127.0.0.1:54321/storage/v1/object/upload/sign/labels/acc/x.jpg?token=t";
const PATH = "acc/x.jpg";
const BARCODE = "8901063201089";
const l = messages.label;

type Seen = { url: string; method: string; headers: Headers; body: unknown };
let seen: Seen[];

function respond(handlers: Record<string, () => Response>) {
  fetchMock.mockImplementation(
    async (input: RequestInfo | URL, init?: RequestInit) => {
      const req =
        input instanceof Request ? input : new Request(String(input), init);
      const text = req.method === "PUT" ? null : await req.clone().text();
      seen.push({
        url: req.url,
        method: req.method,
        headers: req.headers,
        body: text ? JSON.parse(text) : init?.body,
      });
      const key = `${req.method} ${new URL(req.url).pathname}`;
      const h = handlers[key];
      if (!h) throw new Error(`unexpected ${key}`);
      return h();
    },
  );
}

let client: QueryClient;
function view(barcode: string | null = BARCODE) {
  client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <LabelUpload barcode={barcode} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

const photo = () =>
  new File([new Uint8Array(20)], "label.jpg", { type: "image/jpeg" });
const jpeg = new Blob([new Uint8Array(10)], { type: "image/jpeg" });

beforeEach(() => {
  seen = [];
  fetchMock.mockReset();
  router.push.mockReset();
  resize.mockReset();
  resize.mockResolvedValue(jpeg);
  track.mockReset();
});
afterEach(cleanup);

const okHandlers = (
  scanStatus = 200,
  scanBody: unknown = scanDraft("clean"),
) => ({
  "POST /v1/scans/upload-url": () =>
    json(200, { upload_url: SIGNED, path: PATH, expires_in: 120 }),
  "PUT /storage/v1/object/upload/sign/labels/acc/x.jpg": () =>
    new Response("{}", { status: 200 }),
  "POST /v1/scans/label": () => json(scanStatus, scanBody),
});

describe("LabelUpload", () => {
  it("offers the camera (capture=environment), a file picker and a drop zone", () => {
    view();
    const camera = screen.getByLabelText(l.take_photo) as HTMLInputElement;
    expect(camera.type).toBe("file");
    expect(camera.getAttribute("accept")).toBe("image/*");
    expect(camera.getAttribute("capture")).toBe("environment");
    expect(screen.getByLabelText(l.choose_file)).toBeTruthy();
    expect(screen.getByText(l.drop_here)).toBeTruthy();
  });

  it("resize → upload-url → PUT (no bearer) → scans_create_label with the barcode → confirm route", async () => {
    respond(okHandlers());
    view();
    await userEvent.upload(screen.getByLabelText(l.take_photo), photo());
    await waitFor(() =>
      expect(router.push).toHaveBeenCalledWith(
        `/en/scan/confirm/${scanDraft("clean").scan_id}`,
      ),
    );
    expect(resize).toHaveBeenCalledTimes(1);
    const [uploadUrl, put, label] = seen;
    expect(uploadUrl?.body).toEqual({ ext: "jpg" });
    expect(uploadUrl?.headers.get("Authorization")).toBe("Bearer tok");
    expect(put?.method).toBe("PUT");
    expect(put?.url).toBe(SIGNED);
    expect(put?.headers.get("Authorization")).toBeNull();
    expect(put?.headers.get("Content-Type")).toBe("image/jpeg");
    expect(put?.body).toBe(jpeg);
    expect(label?.body).toEqual({ path: PATH, barcode: BARCODE });
    // The draft is handed to the confirm route in memory, with the barcode.
    const cached = getScanDraft(client, scanDraft("clean").scan_id);
    expect(cached?.barcode).toBe(BARCODE);
    expect(cached?.scan.draft.name).toBe("Masala Crunch");
  });

  it("without a barcode, none is sent", async () => {
    respond(okHandlers());
    view(null);
    await userEvent.upload(screen.getByLabelText(l.choose_file), photo());
    await waitFor(() => expect(router.push).toHaveBeenCalled());
    expect(seen[2]?.body).toEqual({ path: PATH });
  });

  it("extraction_failed shows retake and enter-manually; form empty", async () => {
    respond(okHandlers(502, envelope("extraction_failed")));
    view();
    await userEvent.upload(screen.getByLabelText(l.take_photo), photo());
    expect(
      await screen.findByText(messages.error.extraction_failed),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: l.retake })).toBeTruthy();
    expect(
      screen.getByRole("link", { name: l.enter_manually }).getAttribute("href"),
    ).toBe(`/en/scan/manual?barcode=${BARCODE}`);
    // No draft form, nothing prefilled.
    expect(
      screen.queryByRole("button", { name: messages.confirm.save }),
    ).toBeNull();
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(router.push).not.toHaveBeenCalled();
  });

  it("Retake goes back to capture", async () => {
    respond(okHandlers(503, envelope("extraction_unavailable")));
    view();
    await userEvent.upload(screen.getByLabelText(l.take_photo), photo());
    expect(
      await screen.findByText(messages.error.extraction_unavailable),
    ).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: l.retake }));
    expect(
      screen.queryByText(messages.error.extraction_unavailable),
    ).toBeNull();
    expect(screen.getByLabelText(l.take_photo)).toBeTruthy();
  });

  it.each([
    ["image_too_large", 413],
    ["unsupported_image", 415],
    ["rate_limited_scans", 429],
    ["storage_unavailable", 503],
  ] as const)("%s maps to error.%s", async (code, status) => {
    respond(okHandlers(status, envelope(code)));
    view();
    await userEvent.upload(screen.getByLabelText(l.take_photo), photo());
    expect(await screen.findByText(messages.error[code])).toBeTruthy();
  });

  it("a photo the browser can't shrink under 8 MB is image_too_large, nothing uploaded", async () => {
    resize.mockRejectedValue(new ApiError("image_too_large"));
    respond(okHandlers());
    view();
    await userEvent.upload(screen.getByLabelText(l.take_photo), photo());
    expect(
      await screen.findByText(messages.error.image_too_large),
    ).toBeTruthy();
    expect(seen).toHaveLength(0);
  });

  it("analytics: scan_started (method label) on success, no label content", async () => {
    respond(okHandlers());
    view();
    await userEvent.upload(screen.getByLabelText(l.take_photo), photo());
    await waitFor(() => expect(router.push).toHaveBeenCalled());
    expect(track.mock.calls).toEqual([["scan_started", { method: "label" }]]);
  });

  it("analytics: scan_completed with found false on an error", async () => {
    respond(okHandlers(502, envelope("extraction_failed")));
    view();
    await userEvent.upload(screen.getByLabelText(l.take_photo), photo());
    await screen.findByText(messages.error.extraction_failed);
    expect(track.mock.calls).toEqual([
      ["scan_started", { method: "label" }],
      ["scan_completed", { method: "label", found: false }],
    ]);
  });

  it("a draft without confirm hints is never shown", async () => {
    const { confirm: _, ...draft } = scanDraft("clean").draft;
    respond(okHandlers(200, { ...scanDraft("clean"), draft }));
    view();
    await userEvent.upload(screen.getByLabelText(l.take_photo), photo());
    expect(await screen.findByText(messages.error.internal_error)).toBeTruthy();
    expect(router.push).not.toHaveBeenCalled();
    expect(getScanDraft(client, scanDraft("clean").scan_id)).toBeUndefined();
  });

  it("a dropped HEIC file shows unsupported_image before anything is uploaded", async () => {
    resize.mockRejectedValue(new ApiError("unsupported_image"));
    respond(okHandlers());
    view();
    const heic = new File([new Uint8Array(5)], "label.heic", { type: "" });
    fireEvent.drop(screen.getByText(l.drop_here), {
      dataTransfer: { files: [heic] },
    });
    expect(
      await screen.findByText(messages.error.unsupported_image),
    ).toBeTruthy();
    expect(resize).toHaveBeenCalledWith(heic);
    expect(seen).toHaveLength(0);
    expect(screen.getByRole("button", { name: l.retake })).toBeTruthy();
  });

  it("a failed PUT is storage_unavailable and never reaches extraction", async () => {
    respond({
      ...okHandlers(),
      "PUT /storage/v1/object/upload/sign/labels/acc/x.jpg": () =>
        new Response("no", { status: 400 }),
    });
    view();
    await userEvent.upload(screen.getByLabelText(l.take_photo), photo());
    expect(
      await screen.findByText(messages.error.storage_unavailable),
    ).toBeTruthy();
    expect(seen.map((s) => s.method)).toEqual(["POST", "PUT"]);
  });
});
