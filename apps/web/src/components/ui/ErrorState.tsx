import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { buttonClass } from "./Button";
import { AlertTriangleIcon, RefreshIcon } from "./icons";

/**
 * A problem the user can act on. The message is the alert; a retry button
 * (client callers) or retry link (server callers) is offered when given.
 * Styled neutrally: an error is not a verdict, so it never uses verdict colours.
 */
export function ErrorState({
  message,
  onRetry,
  retryHref,
  retrying = false,
  retryLabel,
  children,
  className,
}: {
  message: ReactNode;
  onRetry?: () => void;
  retryHref?: string;
  retrying?: boolean;
  retryLabel?: string;
  /** Extra actions, shown after the retry. */
  children?: ReactNode;
  className?: string;
}) {
  const t = useTranslations();
  const label = retryLabel ?? t("common.retry");
  return (
    <section
      data-testid="error-state"
      className={cn(
        "flex flex-col items-start gap-3 rounded-lg border border-border-default bg-surface-default p-4 shadow-sm sm:p-5",
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-surface-muted text-text-secondary">
          <AlertTriangleIcon />
        </span>
        <p role="alert" className="pt-2 text-md text-text-primary">
          {message}
        </p>
      </div>
      {onRetry || retryHref || children ? (
        <div className="flex flex-wrap gap-2">
          {onRetry ? (
            <button
              type="button"
              disabled={retrying}
              onClick={onRetry}
              className={buttonClass({ variant: "outline" })}
            >
              <RefreshIcon />
              {label}
            </button>
          ) : retryHref ? (
            <a href={retryHref} className={buttonClass({ variant: "outline" })}>
              <RefreshIcon />
              {label}
            </a>
          ) : null}
          {children}
        </div>
      ) : null}
    </section>
  );
}
