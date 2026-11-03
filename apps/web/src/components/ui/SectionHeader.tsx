import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

/** A section title with an optional line of help text and a trailing action. */
export function SectionHeader({
  title,
  description,
  action,
  as: Heading = "h2",
  id,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  as?: "h1" | "h2" | "h3";
  id?: string;
  className?: string;
}) {
  const size =
    Heading === "h1"
      ? "text-xl sm:text-2xl font-bold"
      : Heading === "h2"
        ? "text-lg font-semibold"
        : "text-md font-semibold";
  return (
    <div
      className={cn(
        "flex flex-wrap items-end justify-between gap-x-4 gap-y-2",
        className,
      )}
    >
      <div className="min-w-0 space-y-1">
        <Heading id={id} className={cn(size, "text-text-primary")}>
          {title}
        </Heading>
        {description ? (
          <p className="text-md text-text-secondary">{description}</p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
