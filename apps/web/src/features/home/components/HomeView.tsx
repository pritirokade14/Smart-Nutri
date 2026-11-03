"use client";

import { useQuery } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { pageClass } from "@/components/shell/page";
import { cardClass } from "@/components/ui/Card";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { ErrorState } from "@/components/ui/ErrorState";
import {
  ArrowRightIcon,
  CameraIcon,
  PencilIcon,
  ScanIcon,
} from "@/components/ui/icons";
import { LoadingState } from "@/components/ui/Skeleton";
import { fetchMe } from "@/features/me/api/me";
import { useMembers } from "@/features/members/hooks/useMembers";
import { ModeSwitcher } from "@/features/modes/components/ModeSwitcher";
import { MoreButton } from "@/features/modes/components/MoreMenu";
import { type HomeCard, homeCardsFor } from "@/features/modes/layouts";
import { useActiveMode } from "@/features/modes/useActiveMode";
import { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/cn";
import {
  AllergyCheckCard,
  CustomAlertsSetupCard,
  FamilyStripCard,
} from "./cards/MemberCards";
import { ProteinSwapsCard, TipCard } from "./cards/StaticCards";
import {
  RecentScansCard,
  TodayProteinCard,
  TodaySugarSaltCard,
  WeeklyFamilyCard,
} from "./cards/TodayCards";

// The scan CTAs: identical in every mode, always above the cards.
const ACTIONS = [
  { path: "scan", Icon: ScanIcon, title: "scan.title", body: "home.scan_body" },
  {
    path: "scan/label",
    Icon: CameraIcon,
    title: "label.title",
    body: "home.label_body",
  },
  {
    path: "scan/manual",
    Icon: PencilIcon,
    title: "label.enter_manually",
    body: "home.manual_body",
  },
] as const;

function Cards() {
  const { mode } = useActiveMode();
  const members = useMembers();
  const list = members.data ?? [];
  const primary = list.find((m) => m.is_primary);
  const anyAllergens = list.some((m) => m.allergens.length > 0);
  const render = (card: HomeCard) => {
    switch (card) {
      case "allergy_check":
        return <AllergyCheckCard members={members} mode={mode} />;
      case "today_sugar_salt":
        return <TodaySugarSaltCard primary={primary} />;
      case "today_protein":
        return <TodayProteinCard primary={primary} />;
      case "protein_swaps":
        return <ProteinSwapsCard />;
      case "protein_claims_tip":
      case "claims_tip":
      case "not_covered":
      case "unknown_explainer":
        return <TipCard card={card} />;
      case "family_strip":
        return <FamilyStripCard members={members} />;
      case "weekly_family":
        return <WeeklyFamilyCard />;
      case "custom_alerts_setup":
        return <CustomAlertsSetupCard members={members} />;
      case "recent_scans":
        return <RecentScansCard primary={primary} />;
    }
  };
  return (
    <div className="space-y-4">
      {homeCardsFor(mode, anyAllergens).map((card) => (
        <div key={card}>{render(card)}</div>
      ))}
    </div>
  );
}

/**
 * Home in the account's focused mode (Plan 9, decision 7): the greeting,
 * the mode switcher and More, the scan CTAs (the same in every mode), then
 * the mode's cards from layouts.json, with the allergy card first whenever
 * any member has an allergen (P9-R7). Cards render API values only.
 */
export function HomeView() {
  const t = useTranslations();
  const locale = useLocale();
  const { data, error, isPending, isFetching, refetch } = useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
  });

  if (isPending) {
    return (
      <main className={pageClass}>
        <LoadingState label={t("common.loading")} />
      </main>
    );
  }
  if (error) {
    const code = error instanceof ApiError ? error.code : "internal_error";
    return (
      <main className={pageClass}>
        <ErrorState
          message={
            t.has(`error.${code}`)
              ? t(`error.${code}`)
              : t("error.internal_error")
          }
          onRetry={() => refetch()}
          retrying={isFetching}
        />
      </main>
    );
  }
  return (
    <main className={pageClass}>
      <header className="space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <h1 className="text-xl font-bold text-text-primary sm:text-2xl">
              {t("home.welcome", {
                name: data.display_name ?? data.email ?? "",
              })}
            </h1>
            <p className="text-md text-text-secondary">{t("home.subtitle")}</p>
          </div>
          <MoreButton locale={locale} />
        </div>
        <ModeSwitcher />
      </header>
      <ul className="grid gap-3">
        {ACTIONS.map(({ path, Icon, title, body }, i) => (
          <li key={path}>
            <a
              href={`/${locale}/${path}`}
              className={cn(
                cardClass,
                "group flex items-center gap-4 p-4 transition-colors hover:border-brand-primary sm:p-5",
                i === 0 && "border-brand-primary",
              )}
            >
              <span
                className={cn(
                  "flex size-12 shrink-0 items-center justify-center rounded-lg",
                  i === 0
                    ? "bg-brand-primary text-brand-on"
                    : "bg-brand-soft text-brand-primary",
                )}
              >
                <Icon />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-md font-semibold text-text-primary">
                  {t(title)}
                </span>
                <span className="block text-sm text-text-secondary">
                  {t(body)}
                </span>
              </span>
              <ArrowRightIcon className="size-5 shrink-0 text-text-secondary transition-transform group-hover:translate-x-0.5" />
            </a>
          </li>
        ))}
      </ul>
      <Cards />
      <DisclaimerFooter />
    </main>
  );
}
