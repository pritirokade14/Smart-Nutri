import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { SignOutButton } from "@/components/shell/SignOutButton";
import { EmptyState } from "@/components/ui/EmptyState";
import { UserIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";

// Placeholder until account settings ship (same tab on Android). Sign out
// lives here meanwhile.
export default function ProfilePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations();
  return (
    <main className={pageClass}>
      <SectionHeader as="h1" title={t("profile.title")} />
      <EmptyState
        icon={<UserIcon />}
        title={t("common.coming_soon")}
        description={t("profile.body")}
        action={<SignOutButton />}
      />
    </main>
  );
}
