"use client";

import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  DESTINATION_ICON,
  destinationHref,
} from "@/features/modes/destinations";
import {
  DESTINATION_PATH,
  type Destination,
  moreFor,
  tabsFor,
  type UserType,
} from "@/features/modes/layouts";
import { useActiveMode } from "@/features/modes/useActiveMode";
import { cn } from "@/lib/cn";

// Pages without a tab of their own light the tab they are reached from,
// when that tab is in the bar: results, saved products, search and compare
// come from Scan; adding and editing members happens under Family.
const ALSO: Partial<Record<Destination, readonly string[]>> = {
  scan: ["result", "product", "search", "compare"],
  family: ["members"],
};

/**
 * The tab lit for a path: an exact tab first (in gym mode /compare lights
 * Compare), else the `ALSO` rules among the bar's tabs, else none (a page
 * opened from More shows the bar with no tab selected).
 */
export function activeTab(
  pathname: string,
  tabs: readonly Destination[],
): Destination | null {
  // "/en/scan/label" → "scan"
  const segment = pathname.split("/")[2] ?? "";
  const exact = tabs.find((d) => DESTINATION_PATH[d] === segment);
  if (exact) return exact;
  return tabs.find((d) => ALSO[d]?.includes(segment)) ?? null;
}

function NavLink({
  locale,
  d,
  current,
  bar,
  testId,
}: {
  locale: string;
  d: Destination;
  current: boolean;
  bar: boolean;
  testId?: string;
}) {
  const t = useTranslations("nav");
  const Icon = DESTINATION_ICON[d];
  return (
    <a
      href={destinationHref(locale, d)}
      data-testid={testId}
      aria-current={current ? "page" : undefined}
      className={cn(
        "flex transition-colors",
        bar
          ? "min-h-16 flex-col items-center justify-center gap-1 px-1 text-sm"
          : "min-h-11 items-center gap-3 rounded-full px-4 text-md",
        current
          ? bar
            ? "font-semibold text-brand-primary"
            : "bg-brand-soft font-semibold text-brand-primary"
          : "text-text-secondary hover:bg-surface-muted hover:text-text-primary",
      )}
    >
      {/* size-5 is 24px (the token spacing scale). */}
      <Icon className="size-5 shrink-0" />
      <span className="truncate">{t(d)}</span>
    </a>
  );
}

/**
 * The focused mode's five tabs (packages/test-fixtures/modes/layouts.json):
 * a bottom tab bar on small screens ("bar") and a sidebar rail on wide ones
 * ("rail"). Scan is always second. The rail adds a "More" group with every
 * other destination, so nothing is hidden on wide screens; on small screens
 * More is in the Home header and Profile. The shell renders both; CSS shows
 * one. `mode` overrides the account's active mode (tests).
 */
export function AppNav({
  locale,
  variant,
  mode: forced,
}: {
  locale: string;
  variant: "bar" | "rail";
  mode?: UserType;
}) {
  const t = useTranslations("nav");
  const { mode: active } = useActiveMode();
  const mode = forced ?? active;
  const tabs = tabsFor(mode);
  const pathname = usePathname() ?? "";
  const segment = pathname.split("/")[2] ?? "";
  const current = activeTab(pathname, tabs);
  const bar = variant === "bar";
  return (
    <nav
      aria-label={t("label")}
      className={
        bar
          ? "fixed inset-x-0 bottom-0 z-30 border-t border-border-default bg-surface-default pb-[env(safe-area-inset-bottom)] shadow-sm md:hidden"
          : "sticky top-24 hidden space-y-4 md:block"
      }
    >
      <ul className={bar ? "mx-auto flex max-w-lg" : "flex flex-col gap-1"}>
        {tabs.map((d) => (
          <li key={d} className={bar ? "flex-1" : undefined}>
            <NavLink
              locale={locale}
              d={d}
              current={current === d}
              bar={bar}
              testId="nav-tab"
            />
          </li>
        ))}
      </ul>
      {bar ? null : (
        <div className="space-y-1 border-t border-border-default pt-3">
          <p
            id={`more-${variant}`}
            className="px-4 text-sm font-semibold text-text-secondary"
          >
            {t("more")}
          </p>
          <ul
            aria-labelledby={`more-${variant}`}
            className="flex flex-col gap-1"
          >
            {moreFor(mode).map((d) => (
              <li key={d}>
                <NavLink
                  locale={locale}
                  d={d}
                  current={segment === DESTINATION_PATH[d]}
                  bar={false}
                />
              </li>
            ))}
          </ul>
        </div>
      )}
    </nav>
  );
}
