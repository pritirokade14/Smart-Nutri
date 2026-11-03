"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { InfoIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState } from "@/components/ui/Skeleton";
import type { ApiError } from "@/lib/api/errors";
import { type ConsentPurpose, isGranted } from "../api/members";
import { useConsents, useRecordConsent } from "../hooks/useMembers";
import { errorKey } from "./ConsentDialog";

const PURPOSES: readonly ConsentPurpose[] = ["health_data", "ai_processing"];

/**
 * Profile: each consent's state, with withdraw (or agree). Withdrawing
 * health_data keeps saved allergies and conditions in use (Ruling P5-R20);
 * the notice says so.
 */
export function ConsentSettings() {
  const t = useTranslations();
  const consents = useConsents();
  const record = useRecordConsent();
  const [error, setError] = useState<ApiError | null>(null);

  async function set(purpose: ConsentPurpose, granted: boolean) {
    const state = consents.data?.find((c) => c.purpose === purpose);
    if (!state) return;
    setError(null);
    try {
      await record.mutateAsync({
        purpose,
        version: state.current_version,
        granted,
      });
    } catch (e) {
      setError(e as ApiError);
      void consents.refetch();
    }
  }

  let body: React.ReactNode;
  if (consents.isPending)
    body = <LoadingState label={t("common.loading")} lines={1} />;
  else if (consents.isError)
    body = (
      <ErrorState
        message={t(errorKey(t, consents.error))}
        onRetry={() => consents.refetch()}
        retrying={consents.isFetching}
      />
    );
  else
    body = (
      <ul className="space-y-3">
        {PURPOSES.map((p) => {
          const granted = isGranted(consents.data, p);
          return (
            <Card
              as="li"
              key={p}
              className="space-y-2"
              data-testid={`consent-${p}`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-md font-semibold text-text-primary">
                  {t(`consent.${p}.title`)}
                </h3>
                <span
                  data-testid="consent-state"
                  className="rounded-full bg-surface-muted px-3 py-1 text-sm font-medium text-text-secondary"
                >
                  {granted ? t("consent.granted") : t("consent.not_granted")}
                </span>
              </div>
              <p className="text-sm text-text-secondary">
                {t(`consent.${p}.body`)}
              </p>
              {p === "health_data" && !granted ? (
                <p className="flex gap-2 text-sm text-text-primary">
                  <InfoIcon className="mt-0.5 size-4 shrink-0" />
                  {t("members.consent_withdrawn_notice")}
                </p>
              ) : null}
              <Button
                variant={granted ? "outline" : "secondary"}
                size="sm"
                disabled={record.isPending}
                onClick={() => set(p, !granted)}
              >
                {granted ? t("consent.withdraw") : t("profile.give_consent")}
              </Button>
            </Card>
          );
        })}
      </ul>
    );

  return (
    <section className="space-y-3" aria-labelledby="privacy-title">
      <SectionHeader id="privacy-title" title={t("profile.privacy_title")} />
      {body}
      {error ? (
        <p role="alert" className="text-md text-text-primary">
          {t(errorKey(t, error))}
        </p>
      ) : null}
    </section>
  );
}
