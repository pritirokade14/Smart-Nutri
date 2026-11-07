"use client";

import { useTranslations } from "next-intl";
import { useId, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { useLogMeal } from "@/features/meals/hooks/useMeals";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { track } from "@/lib/analytics";
import type { ApiError } from "@/lib/api/errors";
import type { QuickIn } from "../api/diary";

const FIELDS = [
  ["protein_g", "diary.quick_add.protein", 500],
  ["fat_g", "diary.quick_add.fat", 500],
  ["carbs_g", "diary.quick_add.carbs", 500],
  ["fibre_g", "diary.quick_add.fibre", 200],
] as const;

type Key = (typeof FIELDS)[number][0];

/** A number in range, or null for a blank. `undefined` means invalid. */
function parse(raw: string, max: number): number | null | undefined {
  const s = raw.trim().replace(",", ".");
  if (s === "") return null;
  const n = Number(s);
  return Number.isFinite(n) && n >= 0 && n <= max ? n : undefined;
}

/**
 * Quick add: an optional name, kcal (required) and optional protein, fat,
 * carbs and fibre. A blank is sent as null, never 0 (unknown stays unknown).
 * One client_id serves the whole attempt series, so a retry after a lost
 * response cannot add the entry twice. Offline, the form is kept and the
 * online-only note shows. Analytics get `method` only: never the name or any
 * value.
 */
export function QuickAddForm({
  slotId,
  localDate,
  onLogged,
}: {
  /** The chosen slot; null when the slot list has not loaded (the server picks). */
  slotId: string | null;
  /** Set for a day other than today; today sends none (the server's clock). */
  localDate?: string;
  onLogged: () => void;
}) {
  const t = useTranslations();
  const ids = { name: useId(), energy: useId() };
  const [name, setName] = useState("");
  const [energy, setEnergy] = useState("");
  const [rest, setRest] = useState<Record<Key, string>>({
    protein_g: "",
    fat_g: "",
    carbs_g: "",
    fibre_g: "",
  });
  const [problem, setProblem] = useState<"energy" | "range" | null>(null);
  const clientId = useRef<string | null>(null);
  const log = useLogMeal();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const kcal = parse(energy, 5000);
    if (kcal === null || kcal === undefined || kcal <= 0) {
      setProblem(kcal === undefined ? "range" : "energy");
      return;
    }
    const quick: QuickIn = {
      name: name.trim() === "" ? null : name.trim(),
      energy_kcal: kcal,
    };
    for (const [k, , max] of FIELDS) {
      const v = parse(rest[k], max);
      if (v === undefined) {
        setProblem("range");
        return;
      }
      quick[k] = v;
    }
    setProblem(null);
    clientId.current ??= crypto.randomUUID();
    log.mutate(
      {
        quick,
        ...(slotId ? { meal_slot_id: slotId } : {}),
        ...(localDate ? { local_date: localDate } : {}),
        client_id: clientId.current,
      },
      {
        onSuccess: () => {
          clientId.current = null;
          track("diary_entry_added", { method: "quick_add" });
          onLogged();
        },
      },
    );
  }

  const error = log.error as ApiError | null;
  return (
    <form
      noValidate
      onSubmit={submit}
      data-testid="quick-add-form"
      className="space-y-4"
    >
      <div className="space-y-1">
        <label htmlFor={ids.name} className={labelClass}>
          {t("diary.quick_add.name_label")}
        </label>
        <input
          id={ids.name}
          value={name}
          maxLength={60}
          onChange={(e) => setName(e.target.value)}
          className={inputClass}
        />
      </div>
      <div className="space-y-1">
        <label htmlFor={ids.energy} className={labelClass}>
          {t("diary.quick_add.energy")}
        </label>
        <input
          id={ids.energy}
          inputMode="decimal"
          value={energy}
          aria-invalid={problem !== null || undefined}
          onChange={(e) => setEnergy(e.target.value)}
          className={inputClass}
        />
        {problem === "energy" ? (
          <p role="alert" className={hintClass}>
            {t("error.quick_add_energy_required")}
          </p>
        ) : null}
        {problem === "range" ? (
          <p role="alert" className={hintClass}>
            {t("error.validation_error")}
          </p>
        ) : null}
      </div>
      {FIELDS.map(([k, label]) => (
        <div key={k} className="space-y-1">
          <label htmlFor={`${ids.energy}-${k}`} className={labelClass}>
            {t(label)}
          </label>
          <input
            id={`${ids.energy}-${k}`}
            inputMode="decimal"
            value={rest[k]}
            onChange={(e) => setRest((v) => ({ ...v, [k]: e.target.value }))}
            className={inputClass}
          />
        </div>
      ))}
      <p className={hintClass}>{t("foods.blank_is_unknown")}</p>
      {error ? (
        <p role="alert" className="text-md text-text-primary">
          {error.code === "network"
            ? t("meals.online_only")
            : t(errorKey(t, error))}
        </p>
      ) : null}
      <Button type="submit" disabled={log.isPending}>
        {t("meals.log.save")}
      </Button>
    </form>
  );
}
