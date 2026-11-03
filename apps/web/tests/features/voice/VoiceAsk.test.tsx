import { Blob as NodeBlob, File as NodeFile } from "node:buffer";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { components } from "@smartnutri/api-client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ResultView } from "@/features/analysis/components/ResultView";
import { askVoice, voiceErrorKey } from "@/features/voice/api/askVoice";
import { PushToTalkButton } from "@/features/voice/components/PushToTalkButton";
import { VoiceAnswerPanel } from "@/features/voice/components/VoiceAnswerPanel";
import { VoiceAsk } from "@/features/voice/components/VoiceAsk";
import { resultMessages } from "@/i18n/client-messages";
import { ApiError } from "@/lib/api/errors";
import { analyzeResponse, MESSAGES } from "../../support/analyze-fixtures";
import { envelope, json } from "../../support/api-stub";
import { installMedia } from "./fakes";

type VoiceAnswer = components["schemas"]["VoiceAnswer"];
const fixture = (name: string): VoiceAnswer =>
  JSON.parse(
    readFileSync(
      join(
        process.cwd(),
        `../../packages/test-fixtures/responses/voice/${name}.json`,
      ),
      "utf8",
    ),
  );

vi.mock("next/navigation", () => ({
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
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track, resetAnalytics: vi.fn() }));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

const en = MESSAGES.en;
const MEMBER = "a0000000-0000-4000-8000-000000000001";
const PRODUCT = "62e22ce8-476b-5780-b460-b6230c4c5d6e";

beforeEach(() => {
  fetchMock.mockReset();
  track.mockClear();
  vi.stubEnv("NEXT_PUBLIC_FEATURE_VOICE", "true");
});
afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={resultMessages(en)}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

describe("askVoice", () => {
  // jsdom's FormData/Blob can't be sent through Node's fetch Request; use the
  // runtime's own (what a browser does natively).
  beforeEach(async () => {
    const NodeFormData = (await new Response(new URLSearchParams()).formData())
      .constructor;
    vi.stubGlobal("FormData", NodeFormData);
    vi.stubGlobal("File", NodeFile);
    vi.stubGlobal("Blob", NodeBlob);
  });
  it("askVoice sends multipart with product_id member_id language", async () => {
    let sent: Request | undefined;
    fetchMock.mockImplementation(async (req: Request) => {
      sent = req;
      return json(200, fixture("answer_avoid"));
    });
    const audio = new NodeBlob([new Uint8Array([1, 2, 3])], {
      type: "audio/webm;codecs=opus",
    }) as unknown as Blob;
    const out = await askVoice({
      audio,
      productId: PRODUCT,
      memberId: MEMBER,
      language: "hi",
    });
    expect(out.verdict_status).toBe("avoid");
    expect(sent?.method).toBe("POST");
    expect(new URL(sent?.url ?? "").pathname).toBe("/v1/voice/ask");
    expect(sent?.headers.get("content-type")).toMatch(/^multipart\/form-data/);
    const form = await sent?.formData();
    expect(form?.get("product_id")).toBe(PRODUCT);
    expect(form?.get("member_id")).toBe(MEMBER);
    expect(form?.get("language")).toBe("hi");
    expect(form?.get("barcode")).toBeNull();
    const file = form?.get("audio") as File;
    expect(file.size).toBe(3);
    expect(file.name).toBe("question.webm");
  });

  it("sends the barcode instead for an Open Food Facts product", async () => {
    let sent: Request | undefined;
    fetchMock.mockImplementation(async (req: Request) => {
      sent = req;
      return json(200, fixture("answer_avoid"));
    });
    await askVoice({
      audio: new NodeBlob([new Uint8Array([1])], {
        type: "audio/mp4",
      }) as unknown as Blob,
      barcode: "8901063201089",
      memberId: MEMBER,
      language: "en",
    });
    const form = await sent?.formData();
    expect(form?.get("barcode")).toBe("8901063201089");
    expect(form?.get("product_id")).toBeNull();
    expect((form?.get("audio") as File | undefined)?.name).toBe("question.m4a");
  });

  it("maps API errors to voice messages", () => {
    const k = (code: string) => voiceErrorKey(new ApiError(code));
    expect(k("rate_limited_voice")).toBe("voice.rate_limited");
    expect(k("audio_too_long")).toBe("voice.too_long");
    expect(k("audio_too_large")).toBe("voice.too_long");
    expect(k("voice_not_understood")).toBe("voice.not_understood");
    expect(k("ai_unavailable")).toBe("voice.ai_unavailable");
    expect(k("audio_unsupported")).toBe("error.audio_unsupported");
    expect(k("network")).toBe("error.network");
    expect(k("consent_required")).toBeNull();
  });
});

describe("PushToTalkButton", () => {
  function button(status: "idle" | "recording" | "uploading" = "idle") {
    const handlers = { onStart: vi.fn(), onStop: vi.fn(), onCancel: vi.fn() };
    wrap(<PushToTalkButton status={status} elapsedMs={12_400} {...handlers} />);
    return handlers;
  }

  it("press and hold starts, release sends", () => {
    const h = button();
    const b = screen.getByRole("button", { name: en.voice.button_hold });
    fireEvent.pointerDown(b);
    expect(h.onStart).toHaveBeenCalled();
    cleanup();
    const h2 = button("recording");
    fireEvent.pointerUp(screen.getByRole("button", { pressed: true }));
    expect(h2.onStop).toHaveBeenCalled();
  });

  it("sliding away while recording cancels", () => {
    const h = button("recording");
    fireEvent.pointerLeave(screen.getByRole("button", { pressed: true }));
    expect(h.onCancel).toHaveBeenCalled();
    expect(h.onStop).not.toHaveBeenCalled();
  });

  it("Space toggles: start, then send", () => {
    const h = button();
    fireEvent.keyDown(screen.getByRole("button"), { key: " " });
    expect(h.onStart).toHaveBeenCalled();
    cleanup();
    const h2 = button("recording");
    fireEvent.keyDown(screen.getByRole("button"), { key: " " });
    expect(h2.onStop).toHaveBeenCalled();
  });

  it("shows the timer while recording and is busy while thinking", () => {
    button("recording");
    expect(screen.getByText(en.voice.recording)).toBeTruthy();
    expect(screen.getByText("12 s of 30 s")).toBeTruthy();
    cleanup();
    button("uploading");
    expect(screen.getByText(en.voice.thinking)).toBeTruthy();
    expect((screen.getByRole("button") as HTMLButtonElement).disabled).toBe(
      true,
    );
  });
});

describe("VoiceAnswerPanel", () => {
  it("VoiceAnswerPanel renders verdict token class, answer text, <audio src>, and the disclaimer", () => {
    const a = fixture("answer_avoid");
    wrap(<VoiceAnswerPanel answer={a} />);
    const panel = screen.getByTestId("voice-answer");
    expect(panel.getAttribute("data-verdict")).toBe("avoid");
    expect(within(panel).getByTestId("verdict-badge").textContent).toContain(
      en.status.avoid,
    );
    expect(within(panel).getByText(a.answer)).toBeTruthy();
    expect(
      within(panel).getByText(
        en.voice.you_asked.replace("{question}", a.question),
      ),
    ).toBeTruthy();
    expect(panel.querySelector("audio")?.getAttribute("src")).toBe(a.audio_url);
    expect(within(panel).getByText(en.common.disclaimer)).toBeTruthy();
    expect(
      within(panel).queryByText(en.explanation.source_fallback_note),
    ).toBeNull();
  });

  it("notes when the answer comes from the rules (fallback)", () => {
    wrap(<VoiceAnswerPanel answer={fixture("answer_avoid_fallback")} />);
    expect(screen.getByText(en.explanation.source_fallback_note)).toBeTruthy();
  });

  it("an unexpected status renders as unknown (grey), never ok", () => {
    wrap(
      <VoiceAnswerPanel
        answer={{
          ...fixture("answer_avoid"),
          verdict_status: "great" as VoiceAnswer["verdict_status"],
        }}
      />,
    );
    expect(
      screen.getByTestId("voice-answer").getAttribute("data-verdict"),
    ).toBe("unknown");
  });
});

describe("VoiceAsk", () => {
  async function record(mediaDeny?: string) {
    installMedia(mediaDeny);
    wrap(<VoiceAsk memberId={MEMBER} product={{ productId: PRODUCT }} />);
    const b = screen.getByRole("button", { name: en.voice.button_hold });
    await act(async () => {
      fireEvent.pointerDown(b);
    });
    await act(async () => {
      await new Promise((r) => setTimeout(r, 600));
    });
    await act(async () => {
      fireEvent.pointerUp(screen.getByRole("button"));
    });
  }

  it("records, sends, and shows the answer", async () => {
    fetchMock.mockResolvedValue(json(200, fixture("answer_avoid")));
    await record();
    expect(await screen.findByTestId("voice-answer")).toBeTruthy();
    expect(track).toHaveBeenCalledWith("voice_asked", { language: "en" });
  });

  it("429 shows voice.rate_limited", async () => {
    fetchMock.mockResolvedValue(json(429, envelope("rate_limited_voice")));
    await record();
    expect(await screen.findByText(en.voice.rate_limited)).toBeTruthy();
    expect(screen.queryByTestId("voice-answer")).toBeNull();
  });

  it("a denied mic shows voice.mic_denied and sends nothing", async () => {
    await record("NotAllowedError");
    expect(await screen.findByText(en.voice.mic_denied)).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("voice on the result page", () => {
  function result(flag: string) {
    vi.stubEnv("NEXT_PUBLIC_FEATURE_VOICE", flag);
    const body = analyzeResponse("cola");
    fetchMock.mockImplementation(async () => json(200, body));
    wrap(<ResultView productId={body.product.product_id as string} />);
    return body;
  }

  it("is off by default (NEXT_PUBLIC_FEATURE_VOICE not true)", async () => {
    result("false");
    await waitFor(() =>
      expect(screen.getAllByTestId("verdict-card").length).toBeGreaterThan(0),
    );
    expect(
      screen.queryByRole("button", { name: en.voice.button_hold }),
    ).toBeNull();
  });

  it("with the flag on, offers one button per member", async () => {
    const body = result("true");
    await waitFor(() =>
      expect(screen.getAllByTestId("verdict-card").length).toBe(
        body.verdicts.length,
      ),
    );
    for (const card of screen.getAllByTestId("verdict-card"))
      expect(
        within(card).getByRole("button", { name: en.voice.button_hold }),
      ).toBeTruthy();
  });
});
