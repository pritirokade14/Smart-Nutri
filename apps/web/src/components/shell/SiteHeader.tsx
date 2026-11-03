import type { ReactNode } from "react";
import { LanguageSwitcher } from "./LanguageSwitcher";
import { Logo } from "./Logo";

/** Top bar: logo, language switcher and an optional trailing action. */
export function SiteHeader({
  locale,
  homeHref,
  action,
}: {
  locale: string;
  homeHref: string;
  action?: ReactNode;
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-border-default bg-surface-canvas/90 backdrop-blur supports-[backdrop-filter]:bg-surface-canvas/75">
      <div className="mx-auto flex min-h-16 w-full max-w-6xl items-center justify-between gap-3 px-4 md:px-6">
        <Logo href={homeHref} />
        <div className="flex items-center gap-2">
          <LanguageSwitcher locale={locale} />
          {action}
        </div>
      </div>
    </header>
  );
}

/** Visually hidden until focused: jumps past the header and navigation. */
export function SkipLink({ label }: { label: string }) {
  return (
    <a
      href="#content"
      className="sr-only z-50 rounded-md bg-brand-primary px-4 py-2 text-brand-on focus:not-sr-only focus:fixed focus:top-2 focus:left-2"
    >
      {label}
    </a>
  );
}
