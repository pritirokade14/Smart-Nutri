"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { buttonClass } from "@/components/ui/Button";
import { inputClass, labelClass } from "@/components/ui/field";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export function PhoneOtpForm({ target }: { target: string }) {
  const t = useTranslations("auth");
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const [failed, setFailed] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFailed(false);
    const auth = createSupabaseBrowserClient().auth;
    if (!sent) {
      const { error } = await auth.signInWithOtp({ phone });
      if (error) setFailed(true);
      else setSent(true);
      return;
    }
    const { error } = await auth.verifyOtp({ phone, token: code, type: "sms" });
    if (error) {
      setFailed(true);
      return;
    }
    router.replace(target);
    router.refresh();
  }

  return (
    <form
      onSubmit={submit}
      className="flex flex-col gap-3 rounded-lg border border-border-default bg-surface-muted p-4"
    >
      <label className={`flex flex-col gap-1 ${labelClass}`}>
        {t("phoneLabel")}
        <input
          type="tel"
          required
          autoComplete="tel"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className={inputClass}
        />
      </label>
      {sent && (
        <label className={`flex flex-col gap-1 ${labelClass}`}>
          {t("codeLabel")}
          <input
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className={inputClass}
          />
        </label>
      )}
      <button type="submit" className={buttonClass({ block: true })}>
        {sent ? t("verify") : t("sendCode")}
      </button>
      {failed && (
        <p role="alert" className="text-md text-text-primary">
          {t("error")}
        </p>
      )}
    </form>
  );
}
