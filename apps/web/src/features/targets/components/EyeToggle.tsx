"use client";

import { useTranslations } from "next-intl";
import { EyeIcon, EyeOffIcon } from "@/components/ui/icons";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { TargetsOut } from "../api/targets";
import { useSetDisplay } from "../hooks/useTargets";
import { anyHidden } from "../lib/status";

/**
 * One tap hides or shows every number: show becomes hide_all, anything
 * hidden becomes show (terms-only `targets_display_put`). Targets and the
 * meal summary are refetched afterwards, so the API redacts what it sends.
 */
export function EyeToggle({
  targets,
}: {
  targets: Pick<TargetsOut, "numbers_hidden">;
}) {
  const t = useTranslations();
  const setDisplay = useSetDisplay();
  const hidden = anyHidden(targets);
  const Icon = hidden ? EyeIcon : EyeOffIcon;
  return (
    <>
      <button
        type="button"
        data-testid="eye-toggle"
        aria-label={t(hidden ? "diary.eye.show" : "diary.eye.hide")}
        disabled={setDisplay.isPending}
        className="inline-flex size-11 shrink-0 cursor-pointer items-center justify-center rounded-full text-text-secondary hover:bg-surface-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary disabled:opacity-50"
        onClick={() =>
          setDisplay.mutate({ numbers_display: hidden ? "show" : "hide_all" })
        }
      >
        <Icon />
      </button>
      {/* un-hiding can answer 429 (rate_limited): the standard error copy */}
      {setDisplay.error ? (
        <p
          role="alert"
          data-testid="eye-toggle-error"
          className="basis-full text-sm text-text-primary"
        >
          {t(errorKey(t, setDisplay.error))}
        </p>
      ) : null}
    </>
  );
}
