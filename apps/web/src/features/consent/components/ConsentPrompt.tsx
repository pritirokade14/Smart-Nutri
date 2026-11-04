"use client";

import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { errorKey } from "@/features/members/components/ConsentDialog";
import {
  type ConsentPurpose,
  type ConsentState,
  needsUpdate,
  useGrantConsents,
} from "../api/consent";

/**
 * Asks for consents other than terms: after a gated route refused a call
 * (`consent_required`, e.g. voice needs `ai_processing`), or when a granted
 * consent's text changed (`needs_update`). "Not now" never grants anything.
 */
export function ConsentPrompt({
  states,
  purposes,
  onDone,
  onCancel,
}: {
  states: readonly ConsentState[];
  purposes: readonly ConsentPurpose[];
  onDone: () => void;
  onCancel: () => void;
}) {
  const t = useTranslations();
  const grant = useGrantConsents();
  return (
    <Dialog
      title={t("consent.prompt.title")}
      onClose={onCancel}
      testId="consent-prompt"
      actions={
        <>
          <Button variant="outline" onClick={onCancel}>
            {t("consent.decline")}
          </Button>
          <Button
            disabled={grant.isPending}
            onClick={() =>
              grant.mutate(
                { states, required: purposes },
                { onSuccess: onDone },
              )
            }
          >
            {t("consent.agree")}
          </Button>
        </>
      }
    >
      <p className="text-md text-text-primary">{t("consent.prompt.body")}</p>
      <ul className="space-y-3">
        {purposes.map((p) => (
          <li key={p} className="space-y-1 rounded-md bg-surface-muted p-3">
            <h3 className="text-md font-semibold text-text-primary">
              {t(`consent.${p}.title`)}
            </h3>
            {needsUpdate(states, p) ? (
              <p className="text-sm font-medium text-text-secondary">
                {t("consent.needs_update")}
              </p>
            ) : null}
            <p className="text-sm text-text-primary">
              {t(`consent.${p}.body`)}
            </p>
          </li>
        ))}
      </ul>
      {grant.error ? (
        <p role="alert" className="text-md text-text-primary">
          {t(errorKey(t, grant.error))}
        </p>
      ) : null}
    </Dialog>
  );
}
