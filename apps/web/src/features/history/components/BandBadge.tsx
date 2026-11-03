import { useTranslations } from "next-intl";
import { VerdictIcon, type VerdictStatus } from "@/components/ui/verdict-tone";
import { cn } from "@/lib/cn";
import type { Band } from "../lib/summary";

// A distinct shape per band, so the band never relies on colour alone.
const ICON: Record<Band, VerdictStatus> = {
  ok: "ok",
  near: "caution",
  over: "avoid",
  unknown: "unknown",
};

/** The API's daily-limit band: icon plus label on the band token colour. */
export function BandBadge({
  band,
  className,
}: {
  band: Band;
  className?: string;
}) {
  const t = useTranslations("summary.band");
  return (
    <span
      data-testid="band-badge"
      data-band={band}
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 rounded-full bg-(--band-color) px-3 py-1 text-sm font-semibold text-text-inverse",
        className,
      )}
    >
      <VerdictIcon status={ICON[band]} className="size-4 shrink-0" />
      <span>{t(band)}</span>
    </span>
  );
}
