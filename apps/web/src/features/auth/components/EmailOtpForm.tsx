"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export function EmailOtpForm({ target }: { target: string }) {
  const t = useTranslations("auth");
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const [failed, setFailed] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setFailed(false);
    const auth = createSupabaseBrowserClient().auth;
    if (!sent) {
      const { error } = await auth.signInWithOtp({ email });
      if (error) setFailed(true);
      else setSent(true);
      return;
    }
    const { error } = await auth.verifyOtp({
      email,
      token: code,
      type: "email",
    });
    if (error) {
      setFailed(true);
      return;
    }
    router.replace(target);
    router.refresh();
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-(--spacing-2)">
      <label className="flex flex-col gap-(--spacing-1)">
        {t("emailLabel")}
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-(--radius-sm) border p-(--spacing-2)"
        />
      </label>
      {sent && (
        <label className="flex flex-col gap-(--spacing-1)">
          {t("codeLabel")}
          <input
            inputMode="numeric"
            autoComplete="one-time-code"
            required
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="rounded-(--radius-sm) border p-(--spacing-2)"
          />
        </label>
      )}
      <button
        type="submit"
        className="rounded-(--radius-md) border p-(--spacing-3)"
      >
        {sent ? t("verify") : t("sendCode")}
      </button>
      {failed && <p role="alert">{t("error")}</p>}
    </form>
  );
}
