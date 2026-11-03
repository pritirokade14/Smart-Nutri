"use client";

import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import { GlobeIcon } from "@/components/ui/icons";
import { routing } from "@/i18n/routing";
import { cn } from "@/lib/cn";

/** The current path in another locale: "/en/scan/label" → "/hi/scan/label". */
export function localePath(pathname: string, locale: string): string {
  const parts = pathname.split("/");
  const known = (routing.locales as readonly string[]).includes(parts[1] ?? "");
  const rest = known ? parts.slice(2) : parts.slice(1);
  const tail = rest.filter((p, i) => p !== "" || i < rest.length - 1).join("/");
  return tail ? `/${locale}/${tail}` : `/${locale}`;
}

/**
 * en / hi / mr, each named in its own script. A full page load, so the
 * layout re-renders with the new catalogue; the query string is kept.
 */
export function LanguageSwitcher({
  locale,
  className,
}: {
  locale: string;
  className?: string;
}) {
  const t = useTranslations("language");
  const pathname = usePathname() ?? `/${locale}`;
  return (
    <nav
      aria-label={t("label")}
      className={cn("flex items-center gap-1", className)}
    >
      <GlobeIcon className="hidden size-5 shrink-0 text-text-secondary sm:block" />
      <ul className="flex items-center rounded-full border border-border-default bg-surface-default p-0.5">
        {routing.locales.map((l) => {
          const href = localePath(pathname, l);
          const current = l === locale;
          return (
            <li key={l}>
              <a
                href={href}
                hrefLang={l}
                lang={l}
                aria-current={current ? "true" : undefined}
                onClick={(e) => {
                  const q = window.location.search;
                  if (!q || current) return;
                  e.preventDefault();
                  window.location.assign(href + q);
                }}
                className={cn(
                  "flex min-h-9 items-center rounded-full px-2.5 text-sm transition-colors sm:px-3",
                  current
                    ? "bg-brand-primary font-semibold text-brand-on"
                    : "text-text-secondary hover:bg-surface-muted hover:text-text-primary",
                )}
              >
                {t(l)}
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
