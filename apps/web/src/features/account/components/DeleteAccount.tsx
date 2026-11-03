"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Dialog } from "@/components/ui/Dialog";
import { inputClass } from "@/components/ui/field";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { resetAnalytics, track } from "@/lib/analytics";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";
import { useDeleteAccount } from "../api/account";

/**
 * Profile → Delete account (F11, DPDP erasure). Typing the confirm word
 * enables the button; DELETE /v1/me is retried on 503 (deletion_incomplete),
 * then a Try again is offered. On success every client cache is dropped and
 * the session ends locally (the auth user no longer exists), then goodbye.
 */
export function DeleteAccount({
  retryDelayMs = 1000,
}: {
  retryDelayMs?: number;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const client = useQueryClient();
  const inputId = useId();
  const [open, setOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const word = t("settings.delete_confirm_word");
  const confirmed = typed.trim().toLocaleUpperCase() === word.toUpperCase();

  const remove = useDeleteAccount({
    retryDelayMs,
    onDeleted: async () => {
      client.clear();
      track("account_deleted");
      resetAnalytics();
      // The token outlives the deleted user: end the session now, locally
      // (a server-side sign-out would fail for a user that no longer exists).
      await createSupabaseBrowserClient()
        .auth.signOut({ scope: "local" })
        .catch(() => undefined);
      window.location.assign(`/${locale}/goodbye`);
    },
  });
  const busy = remove.isPending || remove.isSuccess;

  const close = () => {
    if (busy) return;
    setOpen(false);
    setTyped("");
    remove.reset();
  };

  return (
    <section className="space-y-3" aria-labelledby="delete-title">
      <SectionHeader id="delete-title" title={t("settings.delete_title")} />
      <Card className="space-y-3">
        <p className="text-md text-text-primary">{t("settings.delete_body")}</p>
        <Button variant="outline" onClick={() => setOpen(true)}>
          {t("settings.delete_button")}
        </Button>
      </Card>
      {open ? (
        <Dialog
          title={t("settings.delete_dialog_title")}
          onClose={close}
          testId="delete-dialog"
          actions={
            <>
              <Button variant="outline" onClick={close} disabled={busy}>
                {t("settings.delete_cancel")}
              </Button>
              {remove.isError ? (
                <Button onClick={() => remove.mutate()}>
                  {t("common.retry")}
                </Button>
              ) : (
                <Button
                  disabled={!confirmed || busy}
                  onClick={() => confirmed && remove.mutate()}
                >
                  {t("settings.delete_confirm")}
                </Button>
              )}
            </>
          }
        >
          <p className="text-md text-text-primary">
            {t("settings.delete_body")}
          </p>
          <div className="space-y-1">
            <label
              htmlFor={inputId}
              className="block text-md font-semibold text-text-primary"
            >
              {t("settings.delete_confirm_label", { word })}
            </label>
            <input
              id={inputId}
              value={typed}
              onChange={(e) => setTyped(e.target.value)}
              autoComplete="off"
              autoCapitalize="characters"
              spellCheck={false}
              disabled={busy}
              className={inputClass}
            />
          </div>
          {busy ? (
            <p role="status" className="text-md text-text-secondary">
              {remove.failureCount > 0
                ? t("settings.delete_retrying")
                : t("settings.deleting")}
            </p>
          ) : null}
          {remove.isError ? (
            <p role="alert" className="text-md text-text-primary">
              {t(errorKey(t, remove.error))}
            </p>
          ) : null}
        </Dialog>
      ) : null}
    </section>
  );
}
