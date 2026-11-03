"use client";

import { useQueryClient } from "@tanstack/react-query";
import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { type ReactNode, useEffect, useState } from "react";
import { pageClass } from "@/components/shell/page";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import { consentsKey } from "@/features/members/api/members";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { useConsents } from "@/features/members/hooks/useMembers";
import { setConsentRequiredHandler } from "@/lib/api/client";
import { type ConsentPurpose, isGranted, needsUpdate } from "../api/consent";
import { ConsentPrompt } from "./ConsentPrompt";
import { TermsAcceptance } from "./TermsAcceptance";

// Purposes asked for in a dialog over the page (terms has its own full step).
const PROMPTABLE: readonly ConsentPurpose[] = ["health_data", "ai_processing"];

/** Pages that stay reachable without terms: withdraw consents, delete the account. */
function exempt(pathname: string): boolean {
  return pathname.split("/")[2] === "profile";
}

/**
 * Wraps every logged-in page (F11, ADR 0018, ruling G1):
 * - Until `terms` is agreed at the current version, the page is replaced by
 *   the terms and privacy step (first sign-in, or `needs_update`).
 * - A gated route's 403 `consent_required` (anywhere in the app) reloads the
 *   consents and asks for the missing purposes.
 * - A granted consent whose text changed is asked for again, once a session.
 */
export function ConsentGate({ children }: { children: ReactNode }) {
  const t = useTranslations();
  const pathname = usePathname() ?? "";
  const client = useQueryClient();
  const consents = useConsents();
  const [requested, setRequested] = useState<ConsentPurpose[]>([]);
  const [dismissedUpdates, setDismissedUpdates] = useState(false);

  useEffect(
    () =>
      setConsentRequiredHandler((purposes) => {
        void client.invalidateQueries({ queryKey: consentsKey });
        setRequested(purposes);
      }),
    [client],
  );

  if (exempt(pathname)) return children;

  if (consents.isPending)
    return (
      <main className={pageClass}>
        <LoadingState label={t("common.loading")} />
      </main>
    );
  if (consents.isError)
    return (
      <main className={pageClass}>
        <ErrorState
          message={t(errorKey(t, consents.error))}
          onRetry={() => consents.refetch()}
          retrying={consents.isFetching}
        />
      </main>
    );

  const states = consents.data;
  if (!isGranted(states, "terms")) return <TermsAcceptance states={states} />;

  const ask = PROMPTABLE.filter(
    (p) =>
      !isGranted(states, p) &&
      (requested.includes(p) || (!dismissedUpdates && needsUpdate(states, p))),
  );
  const close = () => {
    setRequested([]);
    setDismissedUpdates(true);
  };
  return (
    <>
      {children}
      {ask.length > 0 ? (
        <ConsentPrompt
          states={states}
          purposes={ask}
          onDone={close}
          onCancel={close}
        />
      ) : null}
    </>
  );
}
