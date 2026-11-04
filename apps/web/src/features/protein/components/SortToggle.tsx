"use client";

import { useTranslations } from "next-intl";
import { cn } from "@/lib/cn";

/**
 * A two-option segmented control (default order vs "Higher protein"). The
 * order itself always comes from the API (`sort=protein`); the browser never
 * re-sorts or filters by protein.
 */
export function SortToggle<T extends string>({
  options,
  value,
  onChange,
}: {
  options: readonly { value: T; label: string }[];
  value: T;
  onChange: (next: T) => void;
}) {
  const t = useTranslations("search");
  return (
    <div
      role="radiogroup"
      aria-label={t("sort_label")}
      className="inline-flex flex-wrap gap-1 rounded-full border border-border-default bg-surface-muted p-1"
    >
      {options.map((o) => {
        const on = o.value === value;
        return (
          // biome-ignore lint/a11y/useSemanticElements: a segmented control (radio semantics on buttons)
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange(o.value)}
            className={cn(
              "min-h-9 cursor-pointer rounded-full px-4 text-sm font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary",
              on
                ? "bg-surface-default text-brand-primary shadow-sm"
                : "text-text-secondary hover:text-text-primary",
            )}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
