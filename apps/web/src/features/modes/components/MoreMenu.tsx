"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { ArrowRightIcon, MoreIcon } from "@/components/ui/icons";
import { cn } from "@/lib/cn";
import { DESTINATION_ICON, destinationHref } from "../destinations";
import { moreFor, type UserType } from "../layouts";
import { useActiveMode } from "../useActiveMode";

/**
 * "More" (P9-R6): every destination that is not in the mode's tab bar, so
 * nothing is ever out of reach. Used inline (Profile's first section) and
 * in the Home header's More dialog.
 */
export function MoreList({
  locale,
  mode,
  className,
}: {
  locale: string;
  mode: UserType;
  className?: string;
}) {
  const t = useTranslations("nav");
  return (
    <ul data-testid="more-list" className={cn("grid gap-1", className)}>
      {moreFor(mode).map((d) => {
        const Icon = DESTINATION_ICON[d];
        return (
          <li key={d}>
            <a
              href={destinationHref(locale, d)}
              className="flex min-h-11 items-center gap-3 rounded-md px-3 text-md text-text-primary hover:bg-surface-muted"
            >
              <Icon className="size-5 shrink-0 text-text-secondary" />
              <span className="flex-1">{t(d)}</span>
              <ArrowRightIcon className="size-4 shrink-0 text-text-secondary" />
            </a>
          </li>
        );
      })}
    </ul>
  );
}

/** The active mode's More list (Profile). */
export function ActiveMoreList({ locale }: { locale: string }) {
  const { mode } = useActiveMode();
  return <MoreList locale={locale} mode={mode} />;
}

/** The Home header's "More" button: a dialog with the More list. */
export function MoreButton({ locale }: { locale: string }) {
  const t = useTranslations();
  const { mode } = useActiveMode();
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        <MoreIcon className="size-5 shrink-0" />
        {t("modes.more")}
      </Button>
      {open ? (
        <Dialog
          title={t("modes.more_title")}
          onClose={() => setOpen(false)}
          testId="more-dialog"
          actions={
            <Button variant="outline" onClick={() => setOpen(false)}>
              {t("common.close")}
            </Button>
          }
        >
          <MoreList locale={locale} mode={mode} />
        </Dialog>
      ) : null}
    </>
  );
}
