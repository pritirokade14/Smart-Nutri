"use client";

import type { UseQueryResult } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { buttonClass } from "@/components/ui/Button";
import { chipClass } from "@/components/ui/Chip";
import { InfoIcon, PlusIcon } from "@/components/ui/icons";
import type { MemberOut } from "@/features/members/api/members";
import { isCanonicalAllergen } from "@/features/members/lib/memberForm";
import type { ApiError } from "@/lib/api/errors";
import { CardShell, QueryBody } from "./CardShell";

type Members = UseQueryResult<MemberOut[], ApiError>;

function useMemberName() {
  const t = useTranslations();
  return (m: MemberOut) =>
    m.name || (m.is_primary ? t("members.you_badge") : "");
}

/**
 * Who has which allergy (members_list). Unknown means "could not check",
 * never safe. In the allergy mode with none set, a CTA to add them.
 */
export function AllergyCheckCard({
  members,
  mode,
}: {
  members: Members;
  mode: string;
}) {
  const t = useTranslations();
  const locale = useLocale();
  const name = useMemberName();
  const label = (a: string) =>
    isCanonicalAllergen(a) ? t(`allergen.${a}`) : a;
  return (
    <CardShell card="allergy_check" title={t("home.cards.allergy_check.title")}>
      <QueryBody
        query={members}
        render={(list) => {
          const withAllergies = list.filter((m) => m.allergens.length > 0);
          const primary = list.find((m) => m.is_primary);
          return (
            <div className="space-y-3">
              {withAllergies.length > 0 ? (
                <ul className="space-y-1">
                  {withAllergies.map((m) => (
                    <li key={m.id} className="text-md text-text-primary">
                      {t("home.cards.allergy_check.member_line", {
                        name: name(m),
                        allergens: m.allergens.map(label).join(", "),
                      })}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-md text-text-secondary">
                  {t("home.cards.allergy_check.none")}
                </p>
              )}
              <p className="flex gap-2 text-sm text-text-secondary">
                <InfoIcon className="mt-0.5 size-4 shrink-0" />
                {t("home.cards.allergy_check.unknown_note")}
              </p>
              {withAllergies.length === 0 &&
              mode === "allergy_diet" &&
              primary ? (
                <a
                  href={`/${locale}/members/${primary.id}`}
                  className={buttonClass({ variant: "secondary" })}
                >
                  {t("home.cards.allergy_check.add_cta")}
                </a>
              ) : null}
            </div>
          );
        }}
      />
    </CardShell>
  );
}

/** The family's members and "Add member" (members_list). */
export function FamilyStripCard({ members }: { members: Members }) {
  const t = useTranslations();
  const locale = useLocale();
  const name = useMemberName();
  return (
    <CardShell card="family_strip" title={t("home.cards.family_strip.title")}>
      <QueryBody
        query={members}
        render={(list) => (
          <ul className="flex flex-wrap gap-2">
            {list.map((m) => (
              <li key={m.id}>
                <a href={`/${locale}/members/${m.id}`} className={chipClass}>
                  {name(m)}
                </a>
              </li>
            ))}
            <li>
              <a
                href={`/${locale}/members/new`}
                className={buttonClass({ variant: "secondary", size: "sm" })}
              >
                <PlusIcon className="size-4 shrink-0" />
                {t("home.cards.family_strip.add")}
              </a>
            </li>
          </ul>
        )}
      />
    </CardShell>
  );
}

/** A CTA to switch on ingredient alerts on the account holder's profile. */
export function CustomAlertsSetupCard({ members }: { members: Members }) {
  const t = useTranslations();
  const locale = useLocale();
  const primary = members.data?.find((m) => m.is_primary);
  return (
    <CardShell
      card="custom_alerts_setup"
      title={t("home.cards.custom_alerts_setup.title")}
    >
      <p className="text-md text-text-secondary">
        {t("home.cards.custom_alerts_setup.body")}
      </p>
      <a
        href={`/${locale}/${primary ? `members/${primary.id}` : "family"}`}
        className={buttonClass({ variant: "secondary" })}
      >
        {t("home.cards.custom_alerts_setup.cta")}
      </a>
    </CardShell>
  );
}
