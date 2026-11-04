import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { pageClass } from "@/components/shell/page";
import { InfoIcon } from "@/components/ui/icons";
import * as privacy from "@/content/legal/privacy";
import * as terms from "@/content/legal/terms";
import { localeAlternates, metadataBase } from "@/lib/seo";
import { Markdown } from "./Markdown";

export type LegalKind = "privacy" | "terms";

// The drafts are written in English; hi/mr pages say so and keep the text
// marked lang="en" (machine-translated legal text would be worse than none).
const DOCS = { privacy, terms } as const;

export async function legalMetadata(
  kind: LegalKind,
  locale: string,
): Promise<Metadata> {
  const t = await getTranslations({ locale });
  return {
    metadataBase: metadataBase(),
    title: t(`legal.${kind}_title`),
    description: t(`legal.${kind}_description`),
    alternates: localeAlternates(locale, (l) => `/${l}/${kind}`),
    // Drafts: not indexed until a lawyer signs them off (final-fix I6).
    robots: { index: false, follow: true },
  };
}

/** A public policy page: generic text only, never personal data. */
export async function LegalPage({
  kind,
  locale,
}: {
  kind: LegalKind;
  locale: string;
}) {
  setRequestLocale(locale);
  const t = await getTranslations({ locale });
  const doc = DOCS[kind];
  return (
    <main className={`${pageClass} max-w-3xl px-4 py-8 md:px-6`}>
      <div className="space-y-2">
        <p className="flex items-start gap-2 rounded-md bg-surface-muted px-3 py-2 text-sm text-text-secondary">
          <InfoIcon className="mt-0.5 size-4 shrink-0" />
          <span>{t("legal.draft_notice")}</span>
        </p>
        {locale !== "en" ? (
          <p className="text-sm text-text-secondary">
            {t("legal.english_only")}
          </p>
        ) : null}
        <p className="text-sm text-text-secondary">
          {t("legal.version", { version: doc.version })}
        </p>
      </div>
      <article lang="en" className="space-y-4">
        <Markdown
          source={doc.markdown}
          localeHref={(path) => `/${locale}${path}`}
        />
      </article>
    </main>
  );
}
