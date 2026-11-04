"use client";

import { useTranslations } from "next-intl";
import { errorKey } from "@/features/members/components/ConsentDialog";
import {
  useSetActiveType,
  useUserTypes,
} from "@/features/user-types/hooks/useUserTypes";
import { cn } from "@/lib/cn";
import { byPriority } from "../layouts";

/**
 * The mode switcher (decision 7): a segmented control at the top of Home
 * and in Profile, shown only with two or three types. Switching is
 * optimistic and rolls back on error; it needs no consent and never changes
 * a verdict, a member or a check.
 */
export function ModeSwitcher({ className }: { className?: string }) {
  const t = useTranslations();
  const { data } = useUserTypes();
  const set = useSetActiveType();
  const types = byPriority(data?.types ?? []);
  if (!data || types.length < 2) return null;
  return (
    <div className={cn("space-y-2", className)}>
      <div
        role="radiogroup"
        aria-label={t("modes.switcher_label")}
        className="inline-flex flex-wrap gap-1 rounded-full border border-border-default bg-surface-muted p-1"
      >
        {types.map((type) => {
          const on = data.active_type === type;
          return (
            // biome-ignore lint/a11y/useSemanticElements: a segmented control (radio semantics on buttons)
            <button
              key={type}
              type="button"
              role="radio"
              aria-checked={on}
              onClick={() => {
                if (!on) set.mutate(type);
              }}
              className={cn(
                "min-h-9 cursor-pointer rounded-full px-4 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
                on
                  ? "bg-surface-default text-brand-primary shadow-sm"
                  : "text-text-secondary hover:text-text-primary",
              )}
            >
              {t(`modes.name.${type}`)}
            </button>
          );
        })}
      </div>
      {set.isError ? (
        <p role="alert" className="text-sm text-text-primary">
          {t(errorKey(t, set.error))}
        </p>
      ) : null}
    </div>
  );
}
