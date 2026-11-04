"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { PlusIcon } from "@/components/ui/icons";
import {
  LogMealDialog,
  type LogMealMember,
  type LogMealProduct,
} from "./LogMealDialog";

/** "I ate this" under one member's result card; opens the log dialog for them. */
export function LogMealButton({
  product,
  members,
  memberId,
  memberName,
}: {
  product: LogMealProduct;
  members: readonly LogMealMember[];
  memberId: string;
  /** Makes the button's accessible name unique per member card. */
  memberName?: string;
}) {
  const t = useTranslations("meals.log");
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button
        variant="secondary"
        size="sm"
        data-testid="log-meal-cta"
        aria-label={memberName ? t("cta_for", { name: memberName }) : undefined}
        onClick={() => setOpen(true)}
      >
        <PlusIcon className="size-4" />
        {t("cta")}
      </Button>
      {open ? (
        <LogMealDialog
          product={product}
          members={members}
          memberId={memberId}
          onClose={() => setOpen(false)}
        />
      ) : null}
    </>
  );
}
