import { useTranslations } from "next-intl";
import { LeafIcon } from "@/components/ui/icons";

/** The SmartNutri mark and name, linking home. */
export function Logo({ href }: { href: string }) {
  const t = useTranslations("app");
  return (
    <a
      href={href}
      className="flex min-h-11 shrink-0 items-center gap-2 rounded-md text-md font-bold whitespace-nowrap text-text-primary sm:text-lg"
    >
      <span className="flex size-9 items-center justify-center rounded-md bg-brand-primary text-brand-on">
        <LeafIcon className="size-5" />
      </span>
      <span>{t("name")}</span>
    </a>
  );
}
