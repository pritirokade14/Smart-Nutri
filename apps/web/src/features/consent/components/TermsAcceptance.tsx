"use client";

import { useLocale, useTranslations } from "next-intl";
import { useId, useState } from "react";
import { pageClass } from "@/components/shell/page";
import { SignOutButton } from "@/components/shell/SignOutButton";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { errorKey } from "@/features/members/components/ConsentDialog";
import {
  type ConsentState,
  isGranted,
  needsUpdate,
  useGrantConsents,
} from "../api/consent";

const linkClass =
  "font-semibold text-brand-primary underline underline-offset-4 hover:text-brand-strong";

/**
 * The terms and privacy step after the first sign-in, and again whenever the
 * terms text changes (`needs_update`). Every gated route (analyze, scans,
 * meals, product create) needs `terms` (ruling G1). AI explanations are an
 * optional, unticked extra; health data is asked for when it is first saved.
 */
export function TermsAcceptance({
  states,
}: {
  states: readonly ConsentState[];
}) {
  const t = useTranslations();
  const locale = useLocale();
  const aiId = useId();
  const [ai, setAi] = useState(false);
  const grant = useGrantConsents();
  const updated = needsUpdate(states, "terms");
  const askAi = !isGranted(states, "ai_processing");

  return (
    <main className={pageClass}>
      <Card as="section" data-testid="terms-step" className="space-y-4">
        <h1 className="text-xl font-bold text-text-primary sm:text-2xl">
          {updated
            ? t("consent.terms_step.updated_title")
            : t("consent.terms_step.title")}
        </h1>
        <p className="text-md text-text-primary">
          {updated
            ? t("consent.terms_step.updated_body")
            : t("consent.terms_step.body")}
        </p>
        <ul className="flex flex-wrap gap-x-6 gap-y-2 text-md">
          <li>
            <a
              href={`/${locale}/terms`}
              target="_blank"
              rel="noopener"
              className={linkClass}
            >
              {t("consent.terms_step.read_terms")}
            </a>
          </li>
          <li>
            <a
              href={`/${locale}/privacy`}
              target="_blank"
              rel="noopener"
              className={linkClass}
            >
              {t("consent.terms_step.read_privacy")}
            </a>
          </li>
        </ul>
        <DisclaimerFooter />
        <p className="text-md font-semibold text-text-primary">
          {t("consent.terms.body")}
        </p>
        {askAi ? (
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
        ) : null}
        {grant.error ? (
          <p role="alert" className="text-md text-text-primary">
            {t(errorKey(t, grant.error))}
          </p>
        ) : null}
        <div className="flex flex-wrap gap-2">
          <Button
            disabled={grant.isPending}
            onClick={() =>
              grant.mutate({
                states,
                required: ["terms"],
                optional: ai && askAi ? ["ai_processing"] : [],
              })
            }
          >
            {t("consent.agree")}
          </Button>
          <SignOutButton />
        </div>
        <p className="text-sm text-text-secondary">
          {t("consent.terms_step.leave_note")}{" "}
          <a href={`/${locale}/profile`} className={linkClass}>
            {t("nav.profile")}
          </a>
        </p>
      </Card>
    </main>
  );
}
