"use client";

import { type ReactNode, useEffect, useId, useRef } from "react";
import { cn } from "@/lib/cn";
import { Button } from "./Button";
import { cardClass } from "./Card";

/**
 * A modal dialog: a labelled `role="dialog"` over a dimmed page. Escape and
 * the backdrop call `onClose`; focus moves into the dialog when it opens and
 * back to where it was when it closes.
 */
export function Dialog({
  title,
  children,
  actions,
  onClose,
  testId,
  className,
}: {
  title: ReactNode;
  children?: ReactNode;
  actions: ReactNode;
  onClose: () => void;
  testId?: string;
  className?: string;
}) {
  const titleId = useId();
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const before = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    return () => before?.focus?.();
  }, []);
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
      <button
        type="button"
        aria-hidden="true"
        tabIndex={-1}
        className="absolute inset-0 cursor-default bg-text-primary/40"
        onClick={onClose}
      />
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        data-testid={testId}
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
        }}
        className={cn(
          cardClass,
          "relative max-h-[90vh] w-full max-w-lg space-y-4 overflow-y-auto p-5 focus:outline-none",
          className,
        )}
      >
        <h2 id={titleId} className="text-lg font-semibold text-text-primary">
          {title}
        </h2>
        {children}
        <div className="flex flex-wrap justify-end gap-2">{actions}</div>
      </div>
    </div>
  );
}

/** A yes/no question (e.g. "Remove this allergy?"). */
export function ConfirmDialog({
  message,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
  busy = false,
}: {
  message: ReactNode;
  confirmLabel: string;
  cancelLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
  busy?: boolean;
}) {
  return (
    <Dialog
      title={message}
      onClose={onCancel}
      testId="confirm-dialog"
      actions={
        <>
          <Button variant="outline" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button onClick={onConfirm} disabled={busy}>
            {confirmLabel}
          </Button>
        </>
      }
    />
  );
}
