"use client";

import type { UseQueryResult } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import { errorKey } from "@/features/members/components/ConsentDialog";
import type { HomeCard } from "@/features/modes/layouts";
import type { ApiError } from "@/lib/api/errors";

/** One Home card: a titled surface with a stable test id per card key. */
export function CardShell({
  card,
  title,
  children,
}: {
  card: HomeCard;
  title: string;
  children: ReactNode;
}) {
  return (
    <Card
      as="section"
      data-testid={`home-card-${card}`}
      aria-labelledby={`home-card-${card}-title`}
      className="space-y-3"
    >
      <h2
        id={`home-card-${card}-title`}
        className="text-md font-semibold text-text-primary"
      >
        {title}
      </h2>
      {children}
    </Card>
  );
}

/** Loading and error states for a card's query; `render` gets the data. */
export function QueryBody<T>({
  query,
  render,
}: {
  query: Pick<
    UseQueryResult<T, ApiError>,
    "data" | "error" | "isPending" | "isError" | "isFetching" | "refetch"
  >;
  render: (data: T) => ReactNode;
}) {
  const t = useTranslations();
  if (query.isError)
    return (
      <ErrorState
        message={t(errorKey(t, query.error as ApiError))}
        onRetry={() => void query.refetch()}
        retrying={query.isFetching}
        className="border-none p-0 shadow-none sm:p-0"
      />
    );
  if (query.isPending || query.data === undefined)
    return <LoadingState label={t("common.loading")} />;
  return <>{render(query.data)}</>;
}
