"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

/** Signs out (the providers drop cached results on SIGNED_OUT), then home. */
export function SignOutButton() {
  const t = useTranslations("auth");
  const locale = useLocale();
  const [busy, setBusy] = useState(false);
  return (
    <Button
      variant="outline"
      disabled={busy}
      onClick={async () => {
        setBusy(true);
        await createSupabaseBrowserClient().auth.signOut();
        window.location.assign(`/${locale}`);
      }}
    >
      {t("signOut")}
    </Button>
  );
}
