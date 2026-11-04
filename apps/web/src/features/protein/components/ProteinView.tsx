"use client";

import { useLocale, useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { useId, useState } from "react";
import { Card } from "@/components/ui/Card";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { inputClass, labelClass } from "@/components/ui/field";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { QueryBody } from "@/features/home/components/cards/CardShell";
import { todayIst } from "@/features/meals/api/meals";
import { useSummary } from "@/features/meals/hooks/useMeals";
import { useMembers } from "@/features/members/hooks/useMembers";
import { ProteinProgress } from "./ProteinProgress";

/**
 * The Protein screen (decision 6b): a member picker (the account holder by
 * default) and today's protein against the API's guide, with the no-target
 * note, the kidney note and the disclaimer. `children(memberId)` renders the
 * parts below the progress (higher-protein swaps).
 */
export function ProteinView({
  children,
}: {
  children?: (memberId: string) => ReactNode;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const id = useId();
  const members = useMembers();
  const [picked, setPicked] = useState<string | null>(null);
  const list = members.data ?? [];
  const memberId = picked ?? list.find((m) => m.is_primary)?.id ?? list[0]?.id;
  const member = list.find((m) => m.id === memberId);
  const summary = useSummary(memberId, "day", todayIst());
  return (
    <>
      <SectionHeader as="h1" title={t("protein.title")} />
      <Card className="space-y-4">
        <QueryBody
          query={members}
          render={(ms) => (
            <div className="space-y-1.5">
              <label htmlFor={id} className={labelClass}>
                {t("history.member")}
              </label>
              <select
                id={id}
                className={inputClass}
                value={memberId ?? ""}
                onChange={(e) => setPicked(e.target.value)}
              >
                {ms.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name || (m.is_primary ? t("members.you_badge") : "")}
                  </option>
                ))}
              </select>
            </div>
          )}
        />
        {memberId ? (
          <QueryBody
            query={summary}
            render={(s) => (
              <ProteinProgress
                summary={s}
                member={member}
                locale={locale}
                notes
              />
            )}
          />
        ) : null}
      </Card>
      {memberId && children ? children(memberId) : null}
      <DisclaimerFooter />
    </>
  );
}
