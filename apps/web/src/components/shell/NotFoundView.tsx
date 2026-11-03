import { useTranslations } from "next-intl";
import { buttonClass } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { SearchOffIcon } from "@/components/ui/icons";
import { Logo } from "./Logo";

/** The generic 404 body (unknown page). */
export function NotFoundView({ locale }: { locale: string }) {
  const t = useTranslations();
  return (
    <div className="flex min-h-dvh flex-col items-center gap-8 px-4 py-10 md:py-16">
      <Logo href={`/${locale}`} />
      <main className="w-full max-w-lg">
        <EmptyState
          headingLevel="h1"
          icon={<SearchOffIcon />}
          title={t("error.not_found")}
          description={t("common.not_found_body")}
          action={
            <a href={`/${locale}`} className={buttonClass()}>
              {t("common.go_home")}
            </a>
          }
        />
      </main>
    </div>
  );
}
