"use client";

import { useLocale, useTranslations } from "next-intl";
import { buttonClass } from "@/components/ui/Button";
import { DumbbellIcon } from "@/components/ui/icons";
import { CardShell } from "./CardShell";

type StaticCard =
  | "protein_claims_tip"
  | "claims_tip"
  | "not_covered"
  | "unknown_explainer";

/** Static copy cards: claims tips, "not covered yet", why unknown is not safe. */
export function TipCard({ card }: { card: StaticCard }) {
  const t = useTranslations("home.cards");
  return (
    <CardShell card={card} title={t(`${card}.title`)}>
      <p className="text-md text-text-secondary">{t(`${card}.body`)}</p>
    </CardShell>
  );
}

/** "Find higher-protein options": opens the Protein screen. */
export function ProteinSwapsCard() {
  const t = useTranslations("home.cards.protein_swaps");
  const locale = useLocale();
  return (
    <CardShell card="protein_swaps" title={t("title")}>
      <a
        href={`/${locale}/protein`}
        className={buttonClass({ variant: "secondary" })}
      >
        <DumbbellIcon className="size-5 shrink-0" />
        {t("cta")}
      </a>
    </CardShell>
  );
}
