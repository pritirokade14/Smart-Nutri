"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { safeNext } from "@/lib/auth/safe-next";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";
import { EmailOtpForm } from "./EmailOtpForm";
import { PhoneOtpForm } from "./PhoneOtpForm";

export const buttonClass =
  "w-full rounded-(--radius-md) border p-(--spacing-3) text-(length:--text-md)";

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
    <div className="flex flex-col gap-(--spacing-3)">
      <button type="button" className={buttonClass} onClick={google}>
        {t("google")}
      </button>
      {emailEnabled && (
        <button
          type="button"
          className={buttonClass}
          onClick={() => setMode("email")}
        >
          {t("email")}
        </button>
      )}
      {emailEnabled && mode === "email" && <EmailOtpForm target={target} />}
      {phoneEnabled && (
        <button
          type="button"
          className={buttonClass}
          onClick={() => setMode("phone")}
        >
          {t("phone")}
        </button>
      )}
      {phoneEnabled && mode === "phone" && <PhoneOtpForm target={target} />}
      {failed && <p role="alert">{t("error")}</p>}
    </div>
  );
}
