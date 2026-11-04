"use client";

import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/Dialog";
import { ErrorState } from "@/components/ui/ErrorState";
import { InfoIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState } from "@/components/ui/Skeleton";
import type { ApiError } from "@/lib/api/errors";
import { type ConsentPurpose, isGranted } from "../api/members";
import { useConsents, useRecordConsent } from "../hooks/useMembers";
import { errorKey } from "./ConsentDialog";

const PURPOSES: readonly ConsentPurpose[] = [
  "terms",
  "health_data",
  "ai_processing",
];

const linkClass =
  "font-semibold text-brand-primary underline underline-offset-4 hover:text-brand-strong";

/**
 * Profile: every consent's state, with withdraw, agree, or "review and agree"
 * when its text changed (`needs_update`). Withdrawing terms stops checking
 * and scanning (ruling G1), so it asks first. Withdrawing health_data keeps
 * saved allergies and conditions in use (Ruling P5-R20); the notice says so.
 */
export function ConsentSettings() {
  const t = useTranslations();
  const locale = useLocale();
  const consents = useConsents();
  const record = useRecordConsent();
  const [error, setError] = useState<ApiError | null>(null);
  const [confirmTerms, setConfirmTerms] = useState(false);

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
          const outdated = Boolean(
            consents.data?.find((c) => c.purpose === p)?.needs_update,
          );
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
                  {granted
                    ? t("consent.granted")
                    : outdated
                      ? t("consent.needs_update")
                      : t("consent.not_granted")}
                </span>
              </div>
              <p className="text-sm text-text-secondary">
                {t(`consent.${p}.body`)}
              </p>
              {p === "terms" ? (
                <p className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
                  <a href={`/${locale}/terms`} className={linkClass}>
                    {t("consent.terms_step.read_terms")}
                  </a>
                  <a href={`/${locale}/privacy`} className={linkClass}>
                    {t("consent.terms_step.read_privacy")}
                  </a>
                </p>
              ) : null}
              {p === "health_data" && !granted && !outdated ? (
                <p className="flex gap-2 text-sm text-text-primary">
                  <InfoIcon className="mt-0.5 size-4 shrink-0" />
                  {t("members.consent_withdrawn_notice")}
                </p>
              ) : null}
              <Button
                variant={granted ? "outline" : "secondary"}
                size="sm"
                disabled={record.isPending}
                onClick={() =>
                  granted && p === "terms"
                    ? setConfirmTerms(true)
                    : set(p, !granted)
                }
              >
                {granted
                  ? t("consent.withdraw")
                  : outdated
                    ? t("consent.review_agree")
                    : t("profile.give_consent")}
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
      {confirmTerms ? (
        <ConfirmDialog
          message={t("consent.terms.withdraw_confirm")}
          confirmLabel={t("consent.withdraw")}
          cancelLabel={t("consent.decline")}
          busy={record.isPending}
          onCancel={() => setConfirmTerms(false)}
          onConfirm={() => {
            setConfirmTerms(false);
            void set("terms", false);
          }}
        />
      ) : null}
    </section>
  );
}
