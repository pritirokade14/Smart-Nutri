import { cn } from "@/lib/cn";

/** A pulsing placeholder block. Decorative: pair it with a status message. */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      data-testid="skeleton"
      className={cn(
        "animate-pulse rounded-md bg-surface-muted motion-reduce:animate-none",
        className,
      )}
    />
  );
}

/**
 * A loading placeholder for a page body: a polite status message for screen
 * readers (visually hidden) and skeleton blocks for everyone else.
 */
export function LoadingState({
  label,
  lines = 3,
  className,
}: {
  label: string;
  lines?: number;
  className?: string;
}) {
  return (
    <div className={cn("space-y-3", className)}>
      <p role="status" className="sr-only">
        {label}
      </p>
      <Skeleton className="h-8 w-2/3" />
      {Array.from({ length: lines }, (_, i) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: static placeholder rows
        <Skeleton key={i} className="h-24 w-full rounded-lg" />
      ))}
    </div>
  );
}
