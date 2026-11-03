import { useTranslations } from "next-intl";
import { Logo } from "./Logo";

/** Public footer: brand, tagline and links. Each page shows its own disclaimer. */
export function SiteFooter({ locale }: { locale: string }) {
  const t = useTranslations();
  return (
    <footer className="mt-16 border-t border-border-default bg-surface-default">
      <div className="mx-auto grid w-full max-w-6xl gap-6 px-4 py-10 md:grid-cols-2 md:px-6">
        <div className="space-y-2">
          <Logo href={`/${locale}`} />
          <p className="text-md text-text-secondary">{t("footer.tagline")}</p>
        </div>
        <div className="space-y-3 md:justify-self-end">
          <nav aria-label={t("app.name")}>
            <ul className="flex flex-wrap gap-x-5 gap-y-2 text-sm">
              <li>
                <a
                  href={`/${locale}`}
                  className="text-text-secondary underline-offset-4 hover:text-text-primary hover:underline"
                >
                  {t("nav.home")}
                </a>
              </li>
              <li>
                <a
                  href={`/${locale}/sign-in`}
                  className="text-text-secondary underline-offset-4 hover:text-text-primary hover:underline"
                >
                  {t("auth.title")}
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </footer>
  );
}
