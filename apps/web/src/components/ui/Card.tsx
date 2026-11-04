import type { HTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type CardTag = "div" | "section" | "article" | "li" | "aside";

export const cardClass =
  "rounded-lg border border-border-default bg-surface-default shadow-sm";

/** A raised surface for grouping content. */
export function Card({
  as: Tag = "div",
  padded = true,
  className,
  ...props
}: HTMLAttributes<HTMLElement> & { as?: CardTag; padded?: boolean }) {
  return (
    <Tag
      className={cn(cardClass, padded && "p-4 sm:p-5", className)}
      {...props}
    />
  );
}
