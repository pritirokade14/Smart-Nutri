import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { toneOf, VerdictIcon } from "./verdict-tone";

export type ReasonItem = {
  key: string;
  /** The reason's severity as the API sent it. */
  severity: string;
  content: ReactNode;
};

/**
 * Reasons in the order given, each with its severity icon (shape and colour;
 * an unrecognised severity shows as unknown).
 */
export function ReasonList({
  items,
  id,
  hidden,
  testId,
  className,
}: {
  items: readonly ReasonItem[];
  id?: string;
  hidden?: boolean;
  testId?: string;
  className?: string;
}) {
  return (
    <ul
      id={id}
      hidden={hidden}
      data-testid={testId}
      className={cn("space-y-2", className)}
    >
      {items.map((item) => {
        const tone = toneOf(item.severity);
        return (
          <li
            key={item.key}
            data-verdict={tone}
            className="flex items-start gap-2 text-md text-text-primary"
          >
            <span className="mt-0.5 text-(--verdict-color)">
              <VerdictIcon status={tone} className="size-5 shrink-0" />
            </span>
            <span className="min-w-0">{item.content}</span>
          </li>
        );
      })}
    </ul>
  );
}
