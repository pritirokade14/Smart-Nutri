import { useTranslations } from "next-intl";
import { cn } from "@/lib/cn";

const LINKS = [
  { path: "how-we-score", label: "methodology.title" },
  { path: "privacy", label: "legal.privacy_title" },
  { path: "terms", label: "legal.terms_title" },
] as const;

const linkClass =
  "text-text-secondary underline-offset-4 hover:text-text-primary hover:underline";

/** How we score, Privacy and Terms: in the footer of every page. */
export function LegalLinks({
  locale,
  className,
}: {
  locale: string;
  className?: string;
}) {
  const t = useTranslations();
  return (
    <ul className={cn("flex flex-wrap gap-x-5 gap-y-2 text-sm", className)}>
      {LINKS.map(({ path, label }) => (
        <li key={path}>
          <a href={`/${locale}/${path}`} className={linkClass}>
            {t(label)}
          </a>
        </li>
      ))}
    </ul>
  );
}
