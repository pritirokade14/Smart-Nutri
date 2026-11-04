"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { buttonClass } from "@/components/ui/Button";
import { safeNext } from "@/lib/auth/safe-next";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";
import { EmailOtpForm } from "./EmailOtpForm";
import { PhoneOtpForm } from "./PhoneOtpForm";

// Google sign-in branding: neutral surface, a thin outline, the standard
// multicolour "G" (the official asset, public/google-g.svg) at the left and
// "Continue with Google" as the label.
const googleClass =
  "flex min-h-11 w-full cursor-pointer items-center justify-center gap-3 rounded-full border border-text-secondary/60 bg-surface-default px-4 text-md font-medium text-text-primary transition-colors hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary";

const otherClass = buttonClass({ variant: "outline", block: true });

export function SignInPanel({
  locale,
  next,
}: {
  locale: string;
  next?: string | null;
}) {
  const t = useTranslations("auth");
  const [mode, setMode] = useState<"email" | "phone" | null>(null);
  const [failed, setFailed] = useState(false);
  const target = safeNext(next, `/${locale}/home`);
  const emailEnabled = process.env.NEXT_PUBLIC_FEATURE_EMAIL_OTP === "true";
  const phoneEnabled = process.env.NEXT_PUBLIC_FEATURE_PHONE_OTP === "true";

  async function google() {
    setFailed(false);
    const site = process.env.NEXT_PUBLIC_SITE_URL ?? window.location.origin;
    const { error } = await createSupabaseBrowserClient().auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${site}/auth/callback?next=${encodeURIComponent(target)}`,
      },
    });
    if (error) setFailed(true);
  }

  return (
    <div className="flex flex-col gap-3">
      <button type="button" className={googleClass} onClick={google}>
        {/* biome-ignore lint/performance/noImgElement: a static brand mark; next/image injects inline styles, blocked by our CSP */}
        <img src="/google-g.svg" alt="" width={20} height={20} />
        <span>{t("google")}</span>
      </button>
      {emailEnabled || phoneEnabled ? (
        <div
          aria-hidden="true"
          className="flex items-center gap-3 text-sm text-text-secondary"
        >
          <span className="h-px flex-1 bg-border-default" />
          {t("or")}
          <span className="h-px flex-1 bg-border-default" />
        </div>
      ) : null}
      {emailEnabled && (
        <button
          type="button"
          className={otherClass}
          aria-expanded={mode === "email"}
          onClick={() => setMode("email")}
        >
          {t("email")}
        </button>
      )}
      {emailEnabled && mode === "email" && <EmailOtpForm target={target} />}
      {phoneEnabled && (
        <button
          type="button"
          className={otherClass}
          aria-expanded={mode === "phone"}
          onClick={() => setMode("phone")}
        >
          {t("phone")}
        </button>
      )}
      {phoneEnabled && mode === "phone" && <PhoneOtpForm target={target} />}
      {failed && (
        <p
          role="alert"
          className="rounded-md bg-surface-muted px-3 py-2 text-md text-text-primary"
        >
          {t("error")}
        </p>
      )}
    </div>
  );
}
