"use client";

import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { type ReactNode, useEffect } from "react";
import { pageClass } from "@/components/shell/page";
import { LoadingState } from "@/components/ui/Skeleton";
import { useUserTypes } from "../hooks/useUserTypes";

/** Pages that never redirect to the picker: settings, and the picker itself. */
const EXEMPT = new Set(["profile", "welcome"]);

/**
 * Runs after the terms step (it sits inside ConsentGate, which renders the
 * terms instead of its children until they are agreed). While the account
 * has never answered "What brings you here", every page redirects to
 * /[locale]/welcome. Loading or an error never blocks the app: the page
 * renders (like the terms check on Android), and the default mode applies.
 */
export function UserTypesGate({ children }: { children: ReactNode }) {
  const t = useTranslations("common");
  const pathname = usePathname() ?? "";
  const router = useRouter();
  const [, locale = "en", segment = ""] = pathname.split("/");
  const types = useUserTypes();
  const redirect = types.data?.answered === false && !EXEMPT.has(segment);

  useEffect(() => {
    if (redirect) router.replace(`/${locale}/welcome`);
  }, [redirect, router, locale]);

  if (redirect)
    return (
      <main className={pageClass}>
        <LoadingState label={t("loading")} />
      </main>
    );
  return children;
}
