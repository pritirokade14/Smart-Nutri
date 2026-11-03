"use client";

import { usePathname } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  FamilyIcon,
  HistoryIcon,
  HomeIcon,
  ScanIcon,
  UserIcon,
} from "@/components/ui/icons";
import { cn } from "@/lib/cn";

const TABS = [
  { key: "home", Icon: HomeIcon, also: [] },
  // Results and saved products are reached by scanning.
  { key: "scan", Icon: ScanIcon, also: ["result", "product"] },
  { key: "history", Icon: HistoryIcon, also: [] },
  { key: "family", Icon: FamilyIcon, also: [] },
  { key: "profile", Icon: UserIcon, also: [] },
] as const;

function activeTab(pathname: string): string | null {
  // "/en/scan/label" → "scan"
  const segment = pathname.split("/")[2] ?? "";
  const tab = TABS.find(
    (t) => t.key === segment || (t.also as readonly string[]).includes(segment),
  );
  return tab?.key ?? null;
}

/**
 * The five app tabs: a bottom tab bar on small screens ("bar") and a sidebar
 * rail on wide ones ("rail"). The shell renders both; CSS shows one.
 */
export function AppNav({
  locale,
  variant,
}: {
  locale: string;
  variant: "bar" | "rail";
}) {
  const t = useTranslations("nav");
  const active = activeTab(usePathname() ?? "");
  const bar = variant === "bar";
  return (
    <nav
      aria-label={t("label")}
      className={
        bar
          ? "fixed inset-x-0 bottom-0 z-30 border-t border-border-default bg-surface-default pb-[env(safe-area-inset-bottom)] shadow-sm md:hidden"
          : "sticky top-24 hidden md:block"
      }
    >
      <ul className={bar ? "mx-auto flex max-w-lg" : "flex flex-col gap-1"}>
        {TABS.map(({ key, Icon }) => {
          const current = active === key;
          return (
            <li key={key} className={bar ? "flex-1" : undefined}>
              <a
                href={`/${locale}/${key}`}
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
                <span className="truncate">{t(key)}</span>
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
