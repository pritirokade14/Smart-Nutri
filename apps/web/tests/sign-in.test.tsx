import messages from "@smartnutri/i18n/messages/en.json";
import { render, screen } from "@testing-library/react";
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

afterEach(() => vi.unstubAllEnvs());

describe("SignInPanel", () => {
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
