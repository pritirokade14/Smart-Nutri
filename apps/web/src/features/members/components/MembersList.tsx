"use client";

import { useLocale, useTranslations } from "next-intl";
import { buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/ErrorState";
import { PencilIcon, PlusIcon, UserIcon } from "@/components/ui/icons";
import { LoadingState } from "@/components/ui/Skeleton";
import { useMembers } from "../hooks/useMembers";
import { errorKey } from "./ConsentDialog";

/** Most members per account (the API's member_limit). */
export const MAX_MEMBERS = 10;

/** The account's members: the account holder first, then the family. */
export function MembersList() {
  const t = useTranslations();
  const locale = useLocale();
  const members = useMembers();

  if (members.isPending) return <LoadingState label={t("common.loading")} />;
  if (members.isError)
    return (
      <ErrorState
        message={t(errorKey(t, members.error))}
        onRetry={() => members.refetch()}
        retrying={members.isFetching}
      />
    );

  const full = members.data.length >= MAX_MEMBERS;
  return (
    <div className="space-y-4">
      <ul className="space-y-3" data-testid="members-list">
        {members.data.map((m) => (
          <Card
            as="li"
            key={m.id}
            className="flex items-center gap-4"
            data-testid="member-row"
          >
            <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-brand-soft text-brand-primary">
              <UserIcon />
            </span>
            <div className="min-w-0 flex-1 space-y-0.5">
              <p className="flex flex-wrap items-center gap-2 text-md font-semibold break-words text-text-primary">
                <span>
                  {m.name === "" ? t("members.relation.self") : m.name}
                </span>
                {m.is_primary ? (
                  <span className="rounded-full bg-surface-muted px-2 py-0.5 text-sm font-medium text-text-secondary">
                    {t("members.you_badge")}
                  </span>
                ) : null}
              </p>
              <p className="text-sm text-text-secondary">
                {[
                  m.is_primary ? null : t(`members.relation.${m.relation}`),
                  m.birth_year === null
                    ? null
                    : t("members.born", { year: String(m.birth_year) }),
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            </div>
            <a
              href={`/${locale}/members/${m.id}`}
              className={buttonClass({ variant: "outline", size: "sm" })}
            >
              <PencilIcon className="size-4" />
              {t("members.edit")}
            </a>
          </Card>
        ))}
      </ul>
      {full ? (
        <p className="text-md text-text-secondary">
          {t("members.limit_reached")}
        </p>
      ) : (
        <a
          href={`/${locale}/members/new`}
          className={buttonClass({ size: "lg", block: true })}
        >
          <PlusIcon />
          {t("members.add")}
        </a>
      )}
    </div>
  );
}
