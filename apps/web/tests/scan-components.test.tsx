import messages from "@smartnutri/i18n/messages/en.json";
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const det = vi.hoisted(() => ({
  cb: null as null | ((c: string) => void),
  stop: vi.fn(),
}));
vi.mock("@/features/scan/lib/detector", () => ({
  createDetector: async () => ({
    stop: det.stop,
    onCode: (cb: (c: string) => void) => {
      det.cb = cb;
    },
  }),
}));

import { BarcodeScanner } from "@/features/scan/components/BarcodeScanner";
import { ManualBarcodeForm } from "@/features/scan/components/ManualBarcodeForm";

const wrap = (ui: React.ReactNode) =>
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("ManualBarcodeForm", () => {
  it("shows invalid and does not submit", async () => {
    const onSubmit = vi.fn();
    wrap(<ManualBarcodeForm onSubmit={onSubmit} />);
    await userEvent.type(screen.getByRole("textbox"), "abc123");
    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByText(messages.scan.invalid)).toBeTruthy();
    expect(onSubmit).not.toHaveBeenCalled();
  });
  it("submits the normalized code", async () => {
    const onSubmit = vi.fn();
    wrap(<ManualBarcodeForm onSubmit={onSubmit} />);
    await userEvent.type(screen.getByRole("textbox"), "8901 0632 0108 9");
    await userEvent.click(screen.getByRole("button"));
    expect(onSubmit).toHaveBeenCalledWith("8901063201089");
  });
});

describe("BarcodeScanner", () => {
  const gum = vi.fn();
  beforeEach(() => {
    det.cb = null;
    Object.defineProperty(navigator, "mediaDevices", {
      value: { getUserMedia: gum },
      configurable: true,
    });
    HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
  });

  it("camera_denied on NotAllowedError", async () => {
    gum.mockRejectedValue(new DOMException("x", "NotAllowedError"));
    wrap(<BarcodeScanner onCode={vi.fn()} />);
    expect(await screen.findByText(messages.scan.camera_denied)).toBeTruthy();
  });
  it("camera_unavailable on NotFoundError", async () => {
    gum.mockRejectedValue(new DOMException("x", "NotFoundError"));
    wrap(<BarcodeScanner onCode={vi.fn()} />);
    expect(
      await screen.findByText(messages.scan.camera_unavailable),
    ).toBeTruthy();
  });
  it("fires onCode once and cleans up", async () => {
    gum.mockResolvedValue({ getTracks: () => [] });
    const onCode = vi.fn();
    const { unmount } = wrap(<BarcodeScanner onCode={onCode} />);
    await waitFor(() => expect(det.cb).not.toBeNull());
    act(() => {
      det.cb?.("abc");
      det.cb?.("8901063201089");
      det.cb?.("8901063201089");
    });
    expect(onCode).toHaveBeenCalledTimes(1);
    expect(onCode).toHaveBeenCalledWith("8901063201089");
    unmount();
    expect(det.stop).toHaveBeenCalled();
  });
});
