import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { use } from "react";
import { LanguageSwitcher } from "@/components/shell/LanguageSwitcher";
import { pageClass } from "@/components/shell/page";
import { SignOutButton } from "@/components/shell/SignOutButton";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { DeleteAccount } from "@/features/account/components/DeleteAccount";
import { ConsentSettings } from "@/features/members/components/ConsentSettings";
import { ActiveMoreList } from "@/features/modes/components/MoreMenu";
import { ProfileFocus } from "@/features/user-types/components/ProfileFocus";

// Account settings (same tab on Android): language, every consent (with
// withdraw and re-consent), sign out, and Delete account. Reachable without
// terms (the consent gate exempts it), so a user can always withdraw or erase.
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
      {/* More comes first (P9-R6): every destination not in the tab bar. */}
      <section className="space-y-3" aria-labelledby="more-title">
        <SectionHeader id="more-title" title={t("modes.more_title")} />
        <Card padded={false} className="p-2">
          <ActiveMoreList locale={locale} />
        </Card>
      </section>
      <section className="space-y-3" aria-labelledby="language-title">
        <SectionHeader id="language-title" title={t("language.label")} />
        <Card className="space-y-3">
          <p className="text-md text-text-secondary">
            {t("settings.language_body")}
          </p>
          <LanguageSwitcher locale={locale} />
        </Card>
      </section>
      <ProfileFocus />
      <section className="space-y-3" aria-labelledby="diary-title">
        <SectionHeader id="diary-title" title={t("settings.diary.title")} />
        <Card>
          <a
            href={`/${locale}/profile/guide`}
            data-testid="profile-guide-link"
            className="inline-flex min-h-11 items-center text-md font-semibold text-brand-primary underline-offset-4 hover:underline"
          >
            {t("targets.title")}
          </a>
          <a
            href={`/${locale}/diary?view=progress`}
            data-testid="profile-weight-link"
            className="flex min-h-11 items-center text-md font-semibold text-brand-primary underline-offset-4 hover:underline"
          >
            {t("weight.title")}
          </a>
        </Card>
      </section>
      <ConsentSettings />
      <div>
        <SignOutButton />
      </div>
      <DeleteAccount />
    </main>
  );
}
