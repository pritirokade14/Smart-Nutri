"use client";

import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import type { ApiError } from "@/lib/api/errors";
import { type ConsentPurpose, isGranted } from "../api/members";
import { useConsents, useRecordConsent } from "../hooks/useMembers";

/** i18n key for an API error, falling back to error.internal_error. */
export function errorKey(
  t: { has(key: string): boolean },
  error: ApiError,
): string {
  const key = `error.${error.code}`;
  return t.has(key) ? key : "error.internal_error";
}

/**
 * Asks for health_data consent before member health fields are saved
 * (Ruling P5: only health_data gates saving). AI explanations
 * (ai_processing) are a separate, optional tick: declining them never blocks
 * saving. Each grant is recorded at the current text version from
 * GET /v1/consents; `onAgreed` runs only after health_data is recorded.
 */
export function ConsentDialog({
  onAgreed,
  onCancel,
}: {
  onAgreed: () => void;
  onCancel: () => void;
}) {
  const t = useTranslations();
  const aiId = useId();
  const consents = useConsents();
  const record = useRecordConsent();
  const [ai, setAi] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const aiGranted = isGranted(consents.data, "ai_processing");

  const version = (purpose: ConsentPurpose) =>
    consents.data?.find((c) => c.purpose === purpose)?.current_version;

  async function agree() {
    setError(null);
    const health = version("health_data");
    if (!health) return;
    try {
      await record.mutateAsync({
        purpose: "health_data",
        version: health,
        granted: true,
      });
      const aiVersion = version("ai_processing");
      if (ai && !aiGranted && aiVersion) {
        // Optional: a failure here must not block saving the member.
        await record
          .mutateAsync({
            purpose: "ai_processing",
            version: aiVersion,
            granted: true,
          })
          .catch(() => undefined);
      }
      onAgreed();
    } catch (e) {
      const err = e as ApiError;
      setError(err);
      // The text changed under us: load the current version and ask again.
      if (err.code === "consent_version_mismatch") void consents.refetch();
    }
  }

  return (
    <Dialog
      title={t("consent.health_data.title")}
      onClose={onCancel}
      testId="consent-dialog"
      actions={
        <>
          <Button variant="outline" onClick={onCancel}>
            {t("consent.decline")}
          </Button>
          <Button
            onClick={agree}
            disabled={!version("health_data") || record.isPending}
          >
            {t("consent.agree")}
          </Button>
        </>
      }
    >
      <p className="text-md text-text-primary">
        {t("consent.health_data.body")}
      </p>
      <p className="text-sm text-text-secondary">
        {t("consent.required_note")}
      </p>
      {aiGranted ? null : (
        <div className="flex items-start gap-3 rounded-md bg-surface-muted p-3">
          <input
            id={aiId}
            type="checkbox"
            checked={ai}
            onChange={(e) => setAi(e.target.checked)}
            className="mt-1 size-5 shrink-0"
          />
          <label htmlFor={aiId} className="space-y-1">
            <span className="block text-md font-semibold text-text-primary">
              {t("consent.ai_processing.title")}
            </span>
            <span className="block text-sm text-text-primary">
              {t("consent.ai_processing.body")}
            </span>
            <span className="block text-sm text-text-secondary">
              {t("consent.ai_optional")}
            </span>
          </label>
        </div>
      )}
      {consents.isError ? (
        <p role="alert" className="text-md text-text-primary">
          {t(errorKey(t, consents.error))}
        </p>
      ) : null}
      {error ? (
        <p role="alert" className="text-md text-text-primary">
          {t(errorKey(t, error))}
        </p>
      ) : null}
    </Dialog>
  );
}
