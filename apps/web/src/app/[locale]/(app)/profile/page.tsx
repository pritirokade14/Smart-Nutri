import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { pageClass } from "@/components/shell/page";
import { SignOutButton } from "@/components/shell/SignOutButton";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { ConsentSettings } from "@/features/members/components/ConsentSettings";

// Account settings: each consent's state (with withdraw), and sign out.
// Language and account deletion come later (same tab on Android).
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
      <ConsentSettings />
      <div>
        <SignOutButton />
      </div>
    </main>
  );
}
