import { formatRate, formatWeight } from "@/features/targets/lib/format";

export { formatRate, formatWeight };

/** A calendar date (YYYY-MM-DD) in the locale, Latin digits. Display only. */
export function formatDate(date: string, locale: string): string {
  return new Intl.DateTimeFormat(`${locale}-u-nu-latn`, {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${date}T00:00:00Z`));
}
