import { useLocale, useTranslations } from "next-intl";
import { pageClass } from "@/components/shell/page";
import { buttonClass } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { SearchOffIcon } from "@/components/ui/icons";

// A barcode we have no product for (or not a valid barcode). Served as a 404.
export default function ProductNotFound() {
  const t = useTranslations();
  const locale = useLocale();
  return (
    <main className={`${pageClass} max-w-3xl px-4 py-12 md:py-16`}>
      <EmptyState
        headingLevel="h1"
        icon={<SearchOffIcon />}
        title={t("scan.not_found")}
        description={t("product.not_found_body")}
        action={
          <div className="flex flex-wrap justify-center gap-3">
            <a
              href={`/${locale}/sign-in?next=/${locale}/scan`}
              className={buttonClass()}
            >
              {t("home.scan_cta")}
            </a>
            <a
              href={`/${locale}`}
              className={buttonClass({ variant: "outline" })}
            >
              {t("common.go_home")}
            </a>
          </div>
        }
      />
    </main>
  );
}
