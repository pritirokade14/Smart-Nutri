"use client";

import { useLocale, useTranslations } from "next-intl";
import { buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ModeSwitcher } from "@/features/modes/components/ModeSwitcher";
import { useUserTypes } from "../hooks/useUserTypes";

/**
 * Profile row "What brings you here": the chosen types and a link to edit
 * them (the same picker screens, prefilled). Editing types never changes a
 * member by itself: pre-fill still needs the user's confirmation.
 */
export function ProfileFocus() {
  const t = useTranslations();
  const locale = useLocale();
  const { data } = useUserTypes();
  const names = (data?.types ?? []).map((type) => t(`modes.name.${type}`));
  return (
    <section className="space-y-3" aria-labelledby="focus-title">
      <SectionHeader id="focus-title" title={t("user_types.title")} />
      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {names.length > 0 ? (
            <p className="text-md text-text-primary" data-testid="focus-types">
              {names.join(", ")}
            </p>
          ) : null}
          <a
            href={`/${locale}/welcome?edit=1`}
            className={buttonClass({ variant: "outline" })}
          >
            {t("user_types.edit")}
          </a>
        </div>
        {/* Shown only with two or three types. */}
        <ModeSwitcher />
        <p className="text-sm text-text-secondary">{t("modes.same_checks")}</p>
      </Card>
    </section>
  );
}
