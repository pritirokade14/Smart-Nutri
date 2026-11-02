"use client";

import { useTranslations } from "next-intl";
import { useId, useState } from "react";
import {
  partitionReasons,
  type ReasonOut,
  type VerdictOut,
} from "../lib/reasons";
import { ReasonLine } from "./ReasonLine";

const KNOWN_STATUS = new Set<string>(["ok", "caution", "unknown", "avoid"]);

/**
 * One member's verdict, exactly as the API returned it. The colour comes from
 * CSS keyed on data-status (globals.css: .verdict-card → --color-verdict-*),
 * so the browser never picks or changes a verdict colour.
 *
 * Ruling R22: avoid, unknown and allergen_* reasons are always visible; only
 * the remaining caution/ok reasons sit behind the toggle.
 */
export function VerdictCard({ verdict }: { verdict: VerdictOut }) {
  const t = useTranslations();
  const listId = useId();
  const [open, setOpen] = useState(false);
  // Bare member name, untrimmed (same as Android); "You" only when empty.
  const name =
    verdict.member_name === "" ? t("result.you") : verdict.member_name;
  // An unexpected status string renders as unknown (grey), never ok.
  const status = KNOWN_STATUS.has(verdict.status) ? verdict.status : "unknown";
  const { visible, collapsed } = partitionReasons(verdict.reasons);

  const item = (r: ReasonOut, i: number) => (
    // Reasons have no id; API order is stable for one response.
    <li key={`${i}-${r.code}`}>
      <ReasonLine reason={r} />
    </li>
  );

  return (
    <article
      data-testid="verdict-card"
      data-status={status}
      className="verdict-card space-y-(--spacing-2) rounded-(--radius-md) border p-(--spacing-4)"
    >
      <header className="flex flex-wrap items-center justify-between gap-(--spacing-2)">
        <h2 className="text-(length:--text-lg)">{name}</h2>
        <span className="verdict-badge rounded-(--radius-sm) px-(--spacing-2) py-(--spacing-1) text-(length:--text-md) font-semibold">
          {t(`status.${status}`)}
        </span>
      </header>
      {verdict.profile_set_up === false ? (
        <p
          data-testid="profile-note"
          className="profile-note rounded-(--radius-sm) border border-dashed px-(--spacing-2) py-(--spacing-1) text-(length:--text-sm)"
        >
          {t("verdict.profile_not_set_up")}
        </p>
      ) : null}
      {visible.length > 0 ? (
        <ul
          data-testid="visible-reasons"
          className="list-disc space-y-(--spacing-1) ps-(--spacing-5) text-(length:--text-md)"
        >
          {visible.map(item)}
        </ul>
      ) : null}
      {collapsed.length > 0 ? (
        <div className="text-(length:--text-md)">
          <button
            type="button"
            aria-expanded={open}
            aria-controls={listId}
            onClick={() => setOpen((o) => !o)}
            className="cursor-pointer underline"
          >
            {open ? t("verdict.hide_reasons") : t("verdict.show_all_reasons")}
          </button>
          <ul
            id={listId}
            hidden={!open}
            data-testid="collapsed-reasons"
            className="mt-(--spacing-2) list-disc space-y-(--spacing-1) ps-(--spacing-5)"
          >
            {collapsed.map(item)}
          </ul>
        </div>
      ) : null}
    </article>
  );
}
