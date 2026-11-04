import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { AppNav } from "./AppNav";
import { LegalLinks } from "./LegalLinks";
import { SiteHeader, SkipLink } from "./SiteHeader";

/**
 * Logged-in frame: top header (logo, language), a sidebar rail on wide
 * screens and a bottom tab bar on small ones. Pages render their own <main>.
 */
export function AppShell({
  locale,
  children,
}: {
  locale: string;
  children: ReactNode;
}) {
  const t = useTranslations("common");
  const tf = useTranslations("footer");
  return (
    <div className="min-h-dvh">
      <SkipLink label={t("skip_to_content")} />
      <SiteHeader locale={locale} homeHref={`/${locale}/home`} />
      <div className="mx-auto flex w-full max-w-6xl gap-8 px-4 md:px-6">
        <aside className="w-56 shrink-0 py-6 max-md:hidden">
          <AppNav locale={locale} variant="rail" />
        </aside>
        <div
          id="content"
          tabIndex={-1}
          className="min-w-0 flex-1 pt-5 pb-32 outline-none md:pt-8 md:pb-16"
        >
          {children}
          <footer className="mx-auto mt-12 w-full max-w-2xl border-t border-border-default pt-4">
            <nav aria-label={tf("links_label")}>
              <LegalLinks locale={locale} />
            </nav>
          </footer>
        </div>
      </div>
      <AppNav locale={locale} variant="bar" />
    </div>
  );
}
