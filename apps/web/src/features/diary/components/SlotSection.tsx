"use client";

import { useTranslations } from "next-intl";
import { cardClass } from "@/components/ui/Card";
import { cn } from "@/lib/cn";
import type { MealOut, SlotDayOut } from "../api/diary";
import { slotLabel } from "../lib/slotLabel";
import { EntryRow } from "./EntryRow";

/** One meal slot of the day: its title (the user's own text or a translated default) and its entries. */
export function SlotSection({
  slot,
  onEdit,
  actions,
}: {
  slot: SlotDayOut;
  onEdit: (entry: MealOut) => void;
  actions?: React.ReactNode;
}) {
  const t = useTranslations();
  const title = slotLabel((k) => t(k), {
    labelKey: slot.label_key,
    customLabel: slot.custom_label,
  });
  return (
    <section
      data-testid="slot-section"
      data-slot-id={slot.slot_id}
      aria-label={title}
      className="space-y-2"
    >
      <div className="flex items-center justify-between gap-2">
        <h3
          data-testid="slot-title"
          className="text-md font-semibold text-text-primary"
        >
          {title}
        </h3>
        {slot.archived ? (
          <span
            data-testid="slot-removed"
            className="text-sm text-text-secondary"
          >
            {t("diary.slots.removed")}
          </span>
        ) : null}
        {actions}
      </div>
      {slot.entries.length > 0 ? (
        <ul className={cn(cardClass, "divide-y divide-border-default")}>
          {slot.entries.map((e) => (
            <EntryRow key={e.id} entry={e} onEdit={onEdit} />
          ))}
        </ul>
      ) : null}
    </section>
  );
}
