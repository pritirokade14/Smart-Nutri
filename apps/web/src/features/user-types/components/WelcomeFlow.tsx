"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Button, buttonClass } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState } from "@/components/ui/Skeleton";
import { isGranted } from "@/features/members/api/members";
import {
  ConsentDialog,
  errorKey,
} from "@/features/members/components/ConsentDialog";
import { useConsents } from "@/features/members/hooks/useMembers";
import type { ApiError } from "@/lib/api/errors";
import type {
  FollowUps,
  UserType,
  UserTypesIn,
  UserTypesOut,
} from "../api/userTypes";
import { usePutUserTypes, useUserTypes } from "../hooks/useUserTypes";
import {
  buildBody,
  followUpTypes,
  MAX_TYPES,
  needsHealthConsent,
  needsReview,
  withoutHealth,
} from "../lib/flow";
import { FollowUp } from "./FollowUp";
import { PrefillReview } from "./PrefillReview";
import { TypePicker } from "./TypePicker";

type Step = "pick" | "follow" | "review" | "done";
type After = "home" | "add_member";

/**
 * "What brings you to SmartNutri?" (Plan 9 decisions 1-4): the picker, at
 * most one follow-up per type, then the confirm-only pre-fill review.
 * Shown once right after the terms step, and again from Profile (`edit`).
 * Health tiles or follow-ups need health_data consent before saving; the
 * existing consent dialog opens in place, and declining drops only those.
 * No analytics anywhere in this flow (P9-R8).
 */
export function WelcomeFlow({ edit }: { edit: boolean }) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const current = useUserTypes();
  const consents = useConsents();
  const put = usePutUserTypes();

  const [started, setStarted] = useState(false);
  const [step, setStep] = useState<Step>("pick");
  const [types, setTypes] = useState<UserType[]>([]);
  const [answers, setAnswers] = useState<FollowUps>({});
  const [maxReached, setMaxReached] = useState(false);
  const [note, setNote] = useState<string | undefined>();
  const [saved, setSaved] = useState<UserTypesOut | null>(null);
  const [after, setAfter] = useState<After>("home");
  const [asking, setAsking] = useState<UserTypesIn | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const answered = current.data?.answered;
  // Reachable only while unanswered, or from Profile with ?edit=1.
  useEffect(() => {
    if (answered && !edit && !started) router.replace(`/${locale}/home`);
  }, [answered, edit, started, router, locale]);

  // Editing starts from what is stored (the same screens, prefilled).
  useEffect(() => {
    if (edit && current.data && !started) {
      setTypes([...current.data.types]);
      setAnswers({ ...current.data.follow_ups });
      setStarted(true);
    }
  }, [edit, current.data, started]);

  function finish(to: After) {
    if (to === "add_member") router.push(`/${locale}/members/new`);
    else router.replace(`/${locale}/${edit ? "profile" : "home"}`);
  }

  async function send(body: UserTypesIn, to: After, dropped?: string) {
    setError(null);
    setStarted(true);
    try {
      const out = await put.mutateAsync(body);
      setSaved(out);
      if (needsReview(out.prefill)) setStep("review");
      else if (dropped) setStep("done");
      else finish(to);
    } catch (e) {
      const err = e as ApiError;
      // Consent changed under us: ask in place, as before saving.
      if (err.code === "consent_required") setAsking(body);
      else setError(err);
    }
  }

  function submit(to: After) {
    setAfter(to);
    const body = buildBody(types, answers);
    if (needsHealthConsent(body) && !isGranted(consents.data, "health_data")) {
      setAsking(body);
      return;
    }
    void send(body, to);
  }

  function declined() {
    if (!asking) return;
    const rest = withoutHealth(asking);
    setAsking(null);
    setTypes([...rest.types]);
    setAnswers({ ...rest.follow_ups });
    const dropped = t("user_types.consent_needed");
    setNote(dropped);
    void send(rest, after, dropped);
  }

  function onToggle(type: UserType) {
    if (types.includes(type)) {
      setTypes(types.filter((x) => x !== type));
      setMaxReached(false);
    } else if (types.length >= MAX_TYPES) {
      setMaxReached(true);
    } else {
      setTypes([...types, type]);
      setMaxReached(false);
    }
  }

  if (current.isPending || (edit && !started && !current.isError))
    return <LoadingState label={t("common.loading")} />;
  if (answered && !edit && !started)
    return <LoadingState label={t("common.loading")} />;

  const busy = put.isPending;
  const errorLine = error ? (
    <p role="alert" className="text-md text-text-primary">
      {t(errorKey(t, error))}
    </p>
  ) : null;
  const consent = asking ? (
    <ConsentDialog
      onAgreed={() => {
        const body = asking;
        setAsking(null);
        void send(body, after);
      }}
      onCancel={declined}
    />
  ) : null;

  if (step === "review" && saved?.prefill)
    return (
      <PrefillReview
        prefill={saved.prefill}
        note={note}
        onDone={() => finish(after)}
      />
    );

  if (step === "done")
    return (
      <section className="space-y-4">
        <SectionHeader as="h1" title={t("user_types.saved")} />
        {note ? (
          <p role="status" className="text-md font-medium text-text-primary">
            {note}
          </p>
        ) : null}
        <p className="text-md text-text-secondary">
          {t("user_types.change_later")}
        </p>
        <Button onClick={() => finish(after)}>
          {t("user_types.continue")}
        </Button>
      </section>
    );

  if (step === "follow")
    return (
      <section className="space-y-5">
        <SectionHeader as="h1" title={t("user_types.title")} />
        <FollowUp
          types={types}
          answers={answers}
          onChange={setAnswers}
          onAddMember={() => submit("add_member")}
        />
        {errorLine}
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => submit("home")} disabled={busy}>
            {t("user_types.continue")}
          </Button>
          <Button
            variant="outline"
            onClick={() => setStep("pick")}
            disabled={busy}
          >
            {t("common.cancel")}
          </Button>
        </div>
        {consent}
      </section>
    );

  return (
    <section className="space-y-5">
      <SectionHeader
        as="h1"
        title={t("user_types.title")}
        description={t("user_types.subtitle")}
      />
      {current.isError && edit ? (
        <ErrorState
          message={t(errorKey(t, current.error))}
          onRetry={() => current.refetch()}
          retrying={current.isFetching}
        />
      ) : null}
      <TypePicker
        selected={types}
        onToggle={onToggle}
        maxReached={maxReached}
      />
      {note ? (
        <p role="status" className="text-md font-medium text-text-primary">
          {note}
        </p>
      ) : null}
      <p className="text-sm text-text-secondary">
        {t("user_types.consent_note")}
      </p>
      {errorLine}
      <div className="flex flex-wrap gap-2">
        <Button
          onClick={() =>
            followUpTypes(types).length > 0 ? setStep("follow") : submit("home")
          }
          disabled={types.length === 0 || busy}
        >
          {t("user_types.continue")}
        </Button>
        {edit ? (
          <a
            href={`/${locale}/profile`}
            className={buttonClass({ variant: "outline" })}
          >
            {t("common.cancel")}
          </a>
        ) : (
          <Button
            variant="ghost"
            disabled={busy}
            onClick={() => void send({ types: [], follow_ups: {} }, "home")}
          >
            {t("user_types.skip")}
          </Button>
        )}
      </div>
      <p className="text-sm text-text-secondary">
        {t("user_types.change_later")}
      </p>
      {consent}
    </section>
  );
}
