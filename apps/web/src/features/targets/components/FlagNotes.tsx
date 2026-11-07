"use client";

import { useTranslations } from "next-intl";
import { InfoIcon } from "@/components/ui/icons";
import type { TargetsOut } from "../api/targets";
import { flagMessage } from "../lib/flagMessages";

/** The engine's flags as neutral information notes (never the danger token). */
export function FlagNotes({ targets }: { targets: TargetsOut }) {
  const t = useTranslations();
  const notes = targets.flags
    .map((flag) => ({ flag, text: flagMessage(t, flag, targets) }))
    .filter((n): n is { flag: string; text: string } => n.text !== null);
  if (notes.length === 0) return null;
  return (
    <ul className="space-y-2" data-testid="flag-notes">
      {notes.map((n) => (
        <li
          key={n.flag}
          data-flag={n.flag}
          className="flex gap-2 rounded-md bg-surface-muted p-3 text-sm text-text-primary"
        >
          <InfoIcon className="mt-0.5 size-4 shrink-0" />
          {n.text}
        </li>
      ))}
    </ul>
  );
}
