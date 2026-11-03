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
import { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/cn";

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

export default function HomePage() {
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
      <header className="space-y-1">
        <h1 className="text-xl font-bold text-text-primary sm:text-2xl">
          {t("home.welcome", { name: data.display_name ?? data.email ?? "" })}
        </h1>
        <p className="text-md text-text-secondary">{t("home.subtitle")}</p>
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
      <DisclaimerFooter />
    </main>
  );
}
