"use client";

import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import { ReasonList } from "@/components/ui/ReasonList";
import { VerdictBadge } from "@/components/ui/VerdictBadge";
import { toneOf } from "@/components/ui/verdict-tone";
import {
  partitionReasons,
  type ReasonOut,
  type VerdictOut,
} from "../lib/reasons";
import { ReasonLine } from "./ReasonLine";

/**
 * One member's verdict, exactly as the API returned it. The colour comes from
 * CSS keyed on data-verdict (globals.css → --color-verdict-*, default unknown
 * grey), so the browser never picks or changes a verdict colour; the badge
 * also carries an icon and the status label, so it never relies on colour.
 *
 * Headline (Ruling P5-R24): "<status> for you" for the account holder,
 * otherwise "<status> for <name>". reasons[0], the engine's top reason, leads
 * the visible reasons; avoid, unknown and allergen_* reasons are always
 * visible (R22); only the remaining caution/ok reasons sit behind the toggle.
 */
export function VerdictCard({ verdict }: { verdict: VerdictOut }) {
  const t = useTranslations();
  const listId = useId();
  const [open, setOpen] = useState(false);
  // Bare member name, untrimmed (same as Android); "You" only when empty.
  const name =
    verdict.member_name === "" ? t("result.you") : verdict.member_name;
  // An unexpected status string renders as unknown (grey), never ok.
  const status = toneOf(verdict.status);
  const statusLabel = t(`status.${status}`);
  const headline = verdict.is_primary
    ? t("verdict.for_you", { status: statusLabel })
    : t("verdict.for_member", { status: statusLabel, name });
  const { visible, collapsed } = partitionReasons(verdict.reasons);

  const items = (rs: ReasonOut[]) =>
    rs.map((r, i) => ({
      // Reasons have no id; API order is stable for one response.
      key: `${i}-${r.code}`,
      severity: r.severity,
      content: <ReasonLine reason={r} />,
    }));

  return (
    <article
      data-testid="verdict-card"
      data-status={status}
      data-verdict={status}
      className="overflow-hidden rounded-lg border border-s-[6px] border-border-default border-s-(--verdict-color) bg-surface-default shadow-sm"
    >
      <header className="flex flex-wrap items-center justify-between gap-2 bg-(--verdict-soft) px-4 py-3 sm:px-5">
        <h2 className="min-w-0 text-lg font-semibold break-words text-text-primary">
          {headline}
        </h2>
        <VerdictBadge status={status} />
      </header>
      <div className="space-y-3 px-4 py-4 sm:px-5">
        {verdict.profile_set_up === false ? (
          <p
            data-testid="profile-note"
            className="rounded-md border border-dashed border-text-secondary px-3 py-2 text-sm text-text-secondary"
          >
            {t("verdict.profile_not_set_up")}
          </p>
        ) : null}
        {visible.length > 0 ? (
          <ReasonList items={items(visible)} testId="visible-reasons" />
        ) : null}
        {collapsed.length > 0 ? (
          <div className="space-y-2">
            <button
              type="button"
              aria-expanded={open}
              aria-controls={listId}
              onClick={() => setOpen((o) => !o)}
              className="min-h-11 cursor-pointer text-md font-semibold text-brand-primary underline-offset-4 hover:underline"
            >
              {open ? t("verdict.hide_reasons") : t("verdict.show_all_reasons")}
            </button>
            <ReasonList
              items={items(collapsed)}
              id={listId}
              hidden={!open}
              testId="collapsed-reasons"
            />
          </div>
        ) : null}
      </div>
    </article>
  );
}
