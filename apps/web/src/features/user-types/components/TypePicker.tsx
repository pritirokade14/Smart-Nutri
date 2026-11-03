"use client";

import { useTranslations } from "next-intl";
import { cardClass } from "@/components/ui/Card";
import { CheckCircleIcon } from "@/components/ui/icons";
import { cn } from "@/lib/cn";
import type { UserType } from "../api/userTypes";
import { TILES } from "../lib/flow";

/**
 * The six "What brings you here" tiles: a multi-select of at most three
 * (decision 2). Tapping a fourth shows `user_types.max_reached` instead.
 */
export function TypePicker({
  selected,
  onToggle,
  maxReached,
}: {
  selected: readonly UserType[];
  onToggle: (type: UserType) => void;
  maxReached: boolean;
}) {
  const t = useTranslations("user_types");
  return (
    <div className="space-y-3">
      <p className="text-sm font-medium text-text-secondary">
        {t("pick_up_to")}
      </p>
      <ul className="grid gap-3 sm:grid-cols-2">
        {TILES.map((type) => {
          const on = selected.includes(type);
          return (
            <li key={type}>
              <button
                type="button"
                aria-pressed={on}
                data-testid={`type-tile-${type}`}
                onClick={() => onToggle(type)}
                className={cn(
                  cardClass,
                  "flex h-full w-full cursor-pointer items-start gap-3 p-4 text-start transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
                  on
                    ? "border-brand-primary bg-brand-soft"
                    : "hover:border-brand-primary",
                )}
              >
                <span className="min-w-0 flex-1 space-y-1">
                  <span className="block text-md font-semibold text-text-primary">
                    {t(`tile.${type}.title`)}
                  </span>
                  <span className="block text-sm text-text-secondary">
                    {t(`tile.${type}.subtitle`)}
                  </span>
                </span>
                <CheckCircleIcon
                  className={cn(
                    "size-6 shrink-0",
                    on ? "text-brand-primary" : "text-border-default",
                  )}
                />
              </button>
            </li>
          );
        })}
      </ul>
      {maxReached ? (
        <p role="status" className="text-md font-medium text-text-primary">
          {t("max_reached")}
        </p>
      ) : null}
    </div>
  );
}
