import { useTranslations } from "next-intl";
import { cn } from "@/lib/cn";
import { InfoIcon } from "./icons";

/** "Information, not medical advice." Shown on every result view. */
export function DisclaimerFooter({ className }: { className?: string }) {
  const t = useTranslations();
  return (
    <aside
      data-testid="disclaimer"
      className={cn(
        "flex items-start gap-2 rounded-md bg-surface-muted px-3 py-2 text-sm text-text-secondary",
        className,
      )}
    >
      <InfoIcon className="mt-0.5 size-4 shrink-0" />
      <p>{t("common.disclaimer")}</p>
    </aside>
  );
}
