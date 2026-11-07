import type { ReactNode } from "react";
import { hintClass, labelClass } from "@/components/ui/field";

/** A labelled form field with an optional hint and a neutral error line. */
export function Field({
  id,
  label,
  hint,
  error,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  error?: string | null;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      {children}
      {hint ? (
        <p id={`${id}-hint`} className={hintClass}>
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${id}-error`} className="text-sm font-medium text-text-primary">
          {error}
        </p>
      ) : null}
    </div>
  );
}

/** Describes an input by its hint and error. */
export function describedBy(
  id: string,
  hint: boolean,
  error: boolean,
): string | undefined {
  return (
    [hint ? `${id}-hint` : null, error ? `${id}-error` : null]
      .filter(Boolean)
      .join(" ") || undefined
  );
}
