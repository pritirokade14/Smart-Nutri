import { useTranslations } from "next-intl";
import { cn } from "@/lib/cn";
import { toneOf, VerdictIcon } from "./verdict-tone";

/**
 * The engine's status for one member: icon plus label, on the status colour
 * from the shared tokens. Needs the `status` message namespace (the result
 * pages provide it; public pages never render this).
 */
export function VerdictBadge({
  status,
  size = "md",
  className,
}: {
  status: string;
  size?: "md" | "lg";
  className?: string;
}) {
  const t = useTranslations();
  const tone = toneOf(status);
  return (
    <span
      data-testid="verdict-badge"
      data-verdict={tone}
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 rounded-full bg-(--verdict-color) font-semibold text-text-inverse",
        size === "lg" ? "px-4 py-1.5 text-md" : "px-3 py-1 text-sm",
        className,
      )}
    >
      <VerdictIcon
        status={tone}
        className={size === "lg" ? "size-5 shrink-0" : "size-4 shrink-0"}
      />
      <span>{t(`status.${tone}`)}</span>
    </span>
  );
}
