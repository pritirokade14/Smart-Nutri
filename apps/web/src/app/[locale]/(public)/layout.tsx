import { useTranslations } from "next-intl";
import { use } from "react";
import { SiteFooter } from "@/components/shell/SiteFooter";
import { SiteHeader, SkipLink } from "@/components/shell/SiteHeader";
import { buttonClass } from "@/components/ui/Button";

// Public frame: header (logo, language, sign in), the page, footer. Generic
// content only; nothing here reads a session or personal data.
export default function PublicLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  const t = useTranslations();
  return (
    <div className="flex min-h-dvh flex-col">
      <SkipLink label={t("common.skip_to_content")} />
      <SiteHeader
        locale={locale}
        homeHref={`/${locale}`}
        action={
          <a
            href={`/${locale}/sign-in`}
            className={buttonClass({
              variant: "outline",
              size: "sm",
              className: "max-sm:hidden",
            })}
          >
            {t("auth.title")}
          </a>
        }
      />
      <div id="content" tabIndex={-1} className="flex-1 outline-none">
        {children}
      </div>
      <SiteFooter locale={locale} />
    </div>
  );
}
