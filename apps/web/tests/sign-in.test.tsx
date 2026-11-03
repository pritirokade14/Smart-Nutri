import messages from "@smartnutri/i18n/messages/en.json";
import { cleanup, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SignInPanel } from "@/features/auth/components/SignInPanel";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({ auth: {} }),
}));

const view = () =>
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <SignInPanel locale="en" />
    </NextIntlClientProvider>,
  );

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});

describe("SignInPanel", () => {
  it("email hidden when flag unset", () => {
    vi.stubEnv("NEXT_PUBLIC_FEATURE_EMAIL_OTP", "");
    view();
    expect(screen.queryByText(messages.auth.email)).toBeNull();
    expect(screen.getByText(messages.auth.google)).toBeTruthy();
  });

  it("email hidden when flag false", () => {
    vi.stubEnv("NEXT_PUBLIC_FEATURE_EMAIL_OTP", "false");
    view();
    expect(screen.queryByText(messages.auth.email)).toBeNull();
  });

  it("email shown when flag true", () => {
    vi.stubEnv("NEXT_PUBLIC_FEATURE_EMAIL_OTP", "true");
    view();
    expect(screen.getByText(messages.auth.email)).toBeTruthy();
  });

  it("phone hidden when flag off", () => {
    vi.stubEnv("NEXT_PUBLIC_FEATURE_PHONE_OTP", "false");
    view();
    expect(screen.queryByText(messages.auth.phone)).toBeNull();
    expect(screen.getByText(messages.auth.google)).toBeTruthy();
  });

  it("phone shown when flag on", () => {
    vi.stubEnv("NEXT_PUBLIC_FEATURE_PHONE_OTP", "true");
    view();
    expect(screen.getByText(messages.auth.phone)).toBeTruthy();
  });
});
