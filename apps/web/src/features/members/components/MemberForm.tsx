"use client";

import { useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { type ReactNode, useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/Dialog";
import { hintClass, inputClass, labelClass } from "@/components/ui/field";
import { CloseIcon, InfoIcon } from "@/components/ui/icons";
import type { ApiError } from "@/lib/api/errors";
import { cn } from "@/lib/cn";
import { isGranted, type MemberOut } from "../api/members";
import {
  useConsents,
  useDeleteMember,
  useSaveMember,
} from "../hooks/useMembers";
import {
  CANONICAL_ALLERGENS,
  CONDITIONS,
  CUSTOM_ALERTS,
  DIETS,
  emptyMemberForm,
  GOALS,
  hasAllergen,
  isCanonicalAllergen,
  MAX_ALLERGENS,
  type MemberBody,
  type MemberField,
  type MemberFormErrors,
  type MemberFormValues,
  memberFormSchema,
  memberToForm,
  needsHealthConsent,
  normaliseAllergen,
  RELATIONS,
  SEXES,
  toPatch,
} from "../lib/memberForm";
import { ConsentDialog, errorKey } from "./ConsentDialog";

const toggle = <T,>(list: readonly T[], item: T): T[] =>
  list.includes(item) ? list.filter((x) => x !== item) : [...list, item];

const chipButton =
  "inline-flex min-h-11 cursor-pointer items-center gap-1.5 rounded-full border px-4 text-md font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-primary";
const chipOn = "border-brand-primary bg-brand-soft text-brand-primary";
const chipOff =
  "border-border-default bg-surface-default text-text-primary hover:bg-surface-muted";

function Field({
  id,
  label,
  error,
  help,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  help?: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      {children}
      {help ? (
        <p id={`${id}-help`} className={hintClass}>
          {help}
        </p>
      ) : null}
      {error ? (
        <p id={`${id}-error`} className="text-sm font-medium text-text-primary">
          {error}
        </p>
      ) : null}
    </div>
  );
}

/**
 * Add or edit one family member. Health fields (allergies, conditions, goal,
 * height, weight) are saved only with health_data consent: the consent dialog
 * opens before such a save, and again if the API answers consent_required,
 * then the save is retried. Removing any allergy asks first: a removed
 * allergy is no longer flagged on products.
 */
export function MemberForm({ member }: { member?: MemberOut }) {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const ids = useId();
  const id = (f: string) => `${ids}-${f}`;
  const consents = useConsents();
  const save = useSaveMember();
  const remove = useDeleteMember();
  const isPrimary = member?.is_primary ?? false;
  const healthGranted = isGranted(consents.data, "health_data");

  const [values, setValues] = useState<MemberFormValues>(() =>
    member ? memberToForm(member) : emptyMemberForm(),
  );
  const [errors, setErrors] = useState<MemberFormErrors>({});
  const [other, setOther] = useState("");
  const [otherError, setOtherError] = useState<string | null>(null);
  const [confirmAllergen, setConfirmAllergen] = useState<string | null>(null);
  const [confirmRemoveMember, setConfirmRemoveMember] = useState(false);
  const [consentFor, setConsentFor] = useState<MemberBody | null>(null);
  const [saveError, setSaveError] = useState<ApiError | null>(null);

  const set = <K extends MemberField>(k: K, v: MemberFormValues[K]) =>
    setValues((prev) => ({ ...prev, [k]: v }));
  const errorText = (f: MemberField) =>
    errors[f]
      ? t(errors[f] as string, { year: String(new Date().getFullYear()) })
      : undefined;
  const allergenLabel = (a: string) =>
    isCanonicalAllergen(a) ? t(`allergen.${a}`) : a;
  const familyUrl = `/${locale}/family`;
  // Same fallback as Android: the typed name, else "You" or the relation.
  const displayName = () =>
    values.name.trim() ||
    (isPrimary
      ? t("members.you_badge")
      : t(`members.relation.${values.relation || "other"}`));

  function addAllergen(a: string) {
    if (hasAllergen(values.allergens, a)) return;
    if (values.allergens.length >= MAX_ALLERGENS) {
      setOtherError("members.form.allergen_limit");
      return;
    }
    set("allergens", [...values.allergens, a]);
  }

  function addOther() {
    const a = normaliseAllergen(other);
    if (a === null) {
      setOtherError("members.form.allergen_invalid");
      return;
    }
    setOtherError(null);
    addAllergen(a);
    setOther("");
  }

  async function submitBody(body: MemberBody) {
    setSaveError(null);
    try {
      if (member)
        await save.mutateAsync({
          id: member.id,
          body: toPatch(body, isPrimary, member),
        });
      else await save.mutateAsync({ body });
      router.push(familyUrl);
    } catch (e) {
      const err = e as ApiError;
      // The API is the gate: a 403 opens the consent flow, then retries.
      if (err.code === "consent_required") setConsentFor(body);
      else setSaveError(err);
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = memberFormSchema.safeParse(values);
    if (!parsed.success) {
      setErrors(parsed.errors);
      return;
    }
    setErrors({});
    const body = parsed.data;
    if (needsHealthConsent(body, member) && !healthGranted) {
      setConsentFor(body);
      return;
    }
    void submitBody(body);
  }

  const hasStoredHealth =
    member !== undefined &&
    (member.allergens.length > 0 ||
      member.conditions.length > 0 ||
      member.goal !== null ||
      member.height_cm !== null ||
      member.weight_kg !== null);
  const freeText = values.allergens.filter((a) => !isCanonicalAllergen(a));
  const invalid = (f: MemberField) => (errors[f] ? true : undefined);
  const describedBy = (f: string, help = false) =>
    [
      help ? `${id(f)}-help` : null,
      errors[f as MemberField] ? `${id(f)}-error` : null,
    ]
      .filter(Boolean)
      .join(" ") || undefined;

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-6">
      {consents.isSuccess && !healthGranted && hasStoredHealth ? (
        <p
          data-testid="consent-withdrawn-notice"
          className="flex gap-2 rounded-md bg-surface-muted p-3 text-sm text-text-primary"
        >
          <InfoIcon className="mt-0.5 size-4 shrink-0" />
          {t("members.consent_withdrawn_notice")}
        </p>
      ) : null}

      <Card as="section" className="space-y-4">
        <Field
          id={id("name")}
          label={t("members.form.name")}
          error={errorText("name")}
        >
          <input
            id={id("name")}
            className={inputClass}
            value={values.name}
            maxLength={40}
            autoComplete="off"
            aria-invalid={invalid("name")}
            aria-describedby={describedBy("name")}
            onChange={(e) => set("name", e.target.value)}
          />
        </Field>
        <Field
          id={id("relation")}
          label={t("members.form.relation")}
          error={errorText("relation")}
        >
          <select
            id={id("relation")}
            className={inputClass}
            value={values.relation}
            disabled={isPrimary}
            aria-invalid={invalid("relation")}
            aria-describedby={describedBy("relation")}
            onChange={(e) =>
              set("relation", e.target.value as MemberFormValues["relation"])
            }
          >
            {isPrimary ? (
              <option value="self">{t("members.relation.self")}</option>
            ) : (
              <>
                <option value="">{t("members.form.not_set")}</option>
                {RELATIONS.map((r) => (
                  <option key={r} value={r}>
                    {t(`members.relation.${r}`)}
                  </option>
                ))}
              </>
            )}
          </select>
        </Field>
        <Field
          id={id("birth_year")}
          label={t("members.form.birth_year")}
          help={t("members.form.birth_year_help")}
          error={errorText("birth_year")}
        >
          <input
            id={id("birth_year")}
            className={inputClass}
            inputMode="numeric"
            maxLength={4}
            value={values.birth_year}
            aria-invalid={invalid("birth_year")}
            aria-describedby={describedBy("birth_year", true)}
            onChange={(e) => set("birth_year", e.target.value)}
          />
        </Field>
        <Field id={id("diet")} label={t("members.form.diet")}>
          <select
            id={id("diet")}
            className={inputClass}
            value={values.diet}
            onChange={(e) =>
              set("diet", e.target.value as MemberFormValues["diet"])
            }
          >
            {DIETS.map((d) => (
              <option key={d} value={d}>
                {t(`diet.${d}`)}
              </option>
            ))}
          </select>
        </Field>
        <Field id={id("sex")} label={t("members.form.sex")}>
          <select
            id={id("sex")}
            className={inputClass}
            value={values.sex}
            onChange={(e) =>
              set("sex", e.target.value as MemberFormValues["sex"])
            }
          >
            <option value="">{t("members.form.not_set")}</option>
            {SEXES.map((s) => (
              <option key={s} value={s}>
                {t(`members.sex.${s}`)}
              </option>
            ))}
          </select>
        </Field>
      </Card>

      <Card as="section" className="space-y-5">
        <p className="flex gap-2 text-sm text-text-secondary">
          <InfoIcon className="mt-0.5 size-4 shrink-0" />
          {t("members.form.health_fields_note")}
        </p>

        <fieldset
          className="space-y-3"
          aria-describedby={`${id("allergens")}-help`}
        >
          <legend className={labelClass}>{t("members.form.allergens")}</legend>
          <p id={`${id("allergens")}-help`} className={hintClass}>
            {t("members.form.allergens_help")}
          </p>
          <div className="flex flex-wrap gap-2">
            {CANONICAL_ALLERGENS.map((a) => {
              const on = values.allergens.includes(a);
              return (
                <button
                  key={a}
                  type="button"
                  aria-pressed={on}
                  data-allergen={a}
                  className={cn(chipButton, on ? chipOn : chipOff)}
                  onClick={() => (on ? setConfirmAllergen(a) : addAllergen(a))}
                >
                  {t(`allergen.${a}`)}
                </button>
              );
            })}
          </div>
          {freeText.length > 0 ? (
            <ul className="flex flex-wrap gap-2" data-testid="other-allergens">
              {freeText.map((a) => (
                <li
                  key={a}
                  className={cn(chipButton, chipOn, "cursor-default pe-1")}
                >
                  <span>{a}</span>
                  <button
                    type="button"
                    aria-label={t("members.form.remove_allergy", {
                      allergen: a,
                    })}
                    className="flex size-9 cursor-pointer items-center justify-center rounded-full hover:bg-surface-muted"
                    onClick={() => setConfirmAllergen(a)}
                  >
                    <CloseIcon className="size-4" />
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
          <div className="space-y-1.5">
            <label htmlFor={id("other")} className={labelClass}>
              {t("members.form.allergen_other")}
            </label>
            <div className="flex gap-2">
              <input
                id={id("other")}
                className={inputClass}
                value={other}
                maxLength={60}
                autoComplete="off"
                aria-invalid={otherError ? true : undefined}
                onChange={(e) => setOther(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addOther();
                  }
                }}
              />
              <Button variant="secondary" onClick={addOther}>
                {t("members.form.allergen_add")}
              </Button>
            </div>
            {otherError || errors.allergens ? (
              <p className="text-sm font-medium text-text-primary">
                {t(otherError ?? (errors.allergens as string))}
              </p>
            ) : null}
          </div>
        </fieldset>

        <fieldset className="space-y-2">
          <legend className={labelClass}>{t("members.form.conditions")}</legend>
          {CONDITIONS.map((c) => (
            <label key={c} className="flex min-h-11 items-center gap-3 text-md">
              <input
                type="checkbox"
                className="size-5"
                checked={values.conditions.includes(c)}
                onChange={() => set("conditions", toggle(values.conditions, c))}
              />
              {t(`condition.${c}`)}
            </label>
          ))}
        </fieldset>

        <Field id={id("goal")} label={t("members.form.goal")}>
          <select
            id={id("goal")}
            className={inputClass}
            value={values.goal}
            onChange={(e) =>
              set("goal", e.target.value as MemberFormValues["goal"])
            }
          >
            <option value="">{t("members.form.not_set")}</option>
            {GOALS.map((g) => (
              <option key={g} value={g}>
                {t(`members.goal.${g}`)}
              </option>
            ))}
          </select>
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field
            id={id("height_cm")}
            label={t("members.form.height_cm")}
            error={errorText("height_cm")}
          >
            <input
              id={id("height_cm")}
              className={inputClass}
              inputMode="decimal"
              value={values.height_cm}
              aria-invalid={invalid("height_cm")}
              aria-describedby={describedBy("height_cm")}
              onChange={(e) => set("height_cm", e.target.value)}
            />
          </Field>
          <Field
            id={id("weight_kg")}
            label={t("members.form.weight_kg")}
            error={errorText("weight_kg")}
          >
            <input
              id={id("weight_kg")}
              className={inputClass}
              inputMode="decimal"
              value={values.weight_kg}
              aria-invalid={invalid("weight_kg")}
              aria-describedby={describedBy("weight_kg")}
              onChange={(e) => set("weight_kg", e.target.value)}
            />
          </Field>
        </div>
      </Card>

      <Card as="section" className="space-y-3">
        <fieldset className="space-y-2">
          <legend className={labelClass}>
            {t("members.form.custom_alerts")}
          </legend>
          <p className={hintClass}>{t("members.form.custom_alerts_help")}</p>
          {CUSTOM_ALERTS.map((a) => (
            <label
              key={a}
              className="flex min-h-11 items-center justify-between gap-3 text-md"
            >
              <span className="first-letter:uppercase">{t(`alert.${a}`)}</span>
              <input
                type="checkbox"
                role="switch"
                aria-checked={values.custom_alerts.includes(a)}
                className="size-5"
                checked={values.custom_alerts.includes(a)}
                onChange={() =>
                  set("custom_alerts", toggle(values.custom_alerts, a))
                }
              />
            </label>
          ))}
        </fieldset>
      </Card>

      {saveError ? (
        <p
          role="alert"
          className="rounded-md bg-surface-muted p-3 text-md text-text-primary"
        >
          {t(errorKey(t, saveError))}
        </p>
      ) : null}
      {Object.keys(errors).length > 0 ? (
        <p role="alert" className="text-md font-medium text-text-primary">
          {t("error.validation_error")}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" size="lg" disabled={save.isPending}>
          {t("members.form.save")}
        </Button>
        <Button
          variant="outline"
          size="lg"
          onClick={() => router.push(familyUrl)}
        >
          {t("members.form.cancel")}
        </Button>
        {member && !isPrimary ? (
          <Button
            variant="ghost"
            size="lg"
            className="ms-auto"
            onClick={() => setConfirmRemoveMember(true)}
          >
            {t("members.remove")}
          </Button>
        ) : null}
      </div>

      {confirmAllergen !== null ? (
        <ConfirmDialog
          message={t("members.form.remove_allergy_confirm", {
            allergen: allergenLabel(confirmAllergen),
            name: displayName(),
          })}
          confirmLabel={t("members.remove")}
          cancelLabel={t("members.form.cancel")}
          onCancel={() => setConfirmAllergen(null)}
          onConfirm={() => {
            set(
              "allergens",
              values.allergens.filter((x) => x !== confirmAllergen),
            );
            setConfirmAllergen(null);
          }}
        />
      ) : null}

      {confirmRemoveMember && member ? (
        <ConfirmDialog
          message={t("members.remove_confirm", { name: member.name })}
          confirmLabel={t("members.remove")}
          cancelLabel={t("members.form.cancel")}
          busy={remove.isPending}
          onCancel={() => setConfirmRemoveMember(false)}
          onConfirm={async () => {
            try {
              await remove.mutateAsync(member.id);
              router.push(familyUrl);
            } catch (e) {
              setConfirmRemoveMember(false);
              setSaveError(e as ApiError);
            }
          }}
        />
      ) : null}

      {consentFor !== null ? (
        <ConsentDialog
          onCancel={() => setConsentFor(null)}
          onAgreed={() => {
            const body = consentFor;
            setConsentFor(null);
            void submitBody(body);
          }}
        />
      ) : null}
    </form>
  );
}
