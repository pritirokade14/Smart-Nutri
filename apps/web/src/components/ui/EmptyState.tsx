import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { cardClass } from "./Card";

/** A friendly placeholder: icon, title, a line of text and an optional action. */
export function EmptyState({
  icon,
  title,
  description,
  badge,
  action,
  headingLevel = "h2",
  className,
}: {
  icon?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  /** A small pill above the title, e.g. "Coming soon". */
  badge?: ReactNode;
  action?: ReactNode;
  headingLevel?: "h1" | "h2" | "h3";
  className?: string;
}) {
  const Heading = headingLevel;
  return (
    <section
      data-testid="empty-state"
      className={cn(
        cardClass,
        "flex flex-col items-center gap-3 px-5 py-10 text-center",
        className,
      )}
    >
      {icon ? (
        <div className="flex size-16 items-center justify-center rounded-full bg-brand-soft text-brand-primary [&>svg]:size-8">
          {icon}
        </div>
      ) : null}
      {badge ? (
        <span className="rounded-full bg-surface-muted px-3 py-1 text-sm font-semibold text-text-secondary">
          {badge}
        </span>
      ) : null}
      <Heading className="text-lg font-semibold text-text-primary">
        {title}
      </Heading>
      {description ? (
        <p className="max-w-md text-md text-text-secondary">{description}</p>
      ) : null}
      {action ? <div className="pt-2">{action}</div> : null}
    </section>
  );
}
