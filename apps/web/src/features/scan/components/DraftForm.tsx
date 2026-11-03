"use client";

import { useTranslations } from "next-intl";
import { type ReactNode, useId, useMemo, useRef, useState } from "react";
import {
  BASES,
  type Basis,
  CATEGORIES,
  type Category,
  type ConfirmableField,
  type DraftFormValues,
  type DraftNutrients,
  draftSchema,
  NUTRIENT_FIELDS,
  type NumberInput,
  type NutrientField,
  type ProductCreate,
  type ProductDraft,
  parseNumberInput,
  SODIUM_UNITS,
  type SodiumUnit,
  type VegMark,
} from "../lib/draftSchema";
import {
  hasWarning,
  highlightedFields,
  sodiumUnitUnconfirmed,
} from "../lib/warnings";
import { WarningBanner } from "./WarningBanner";

export type ServerFieldError = { code: string; fields: string[] };

type Column = Record<NutrientField, NumberInput>;
type Item = { id: number; text: string };

const EMPTY_COLUMN = Object.fromEntries(
  NUTRIENT_FIELDS.map((f) => [f, null]),
) as Column;

const KNOWN_FIELDS = new Set<string>([
  ...NUTRIENT_FIELDS,
  "serving_size_g",
  "name",
  "brand",
  "category",
  "basis",
  "sodium_unit",
  "ingredients",
  "allergen_statement",
  "may_contain_statement",
  "claims",
  "veg_mark",
]);

/** "body.nutrients.sugars_g" / "ingredients.3" → the form field it names. */
export function formFieldOf(path: string): string | null {
  const parts = path.split(".");
  for (let i = parts.length - 1; i >= 0; i--) {
    const p = parts[i];
    if (p && KNOWN_FIELDS.has(p)) return p;
  }
  return null;
}

function column(n: DraftNutrients | null | undefined): Column {
  if (!n) return { ...EMPTY_COLUMN };
  return Object.fromEntries(
    NUTRIENT_FIELDS.map((f) => [f, n[f] ?? null]),
  ) as Column;
}

/** The printed number as the input shows it; float noise stripped, no rounding. */
function shown(v: NumberInput): string {
  if (v === null) return "";
  if (typeof v === "number") return String(Number(v.toPrecision(12)));
  return v;
}

type Init = {
  columns: Record<Basis, Column>;
  basis: Basis | "";
  category: Category | "";
  serving: NumberInput;
};

function initial(draft: ProductDraft | null): Init {
  if (!draft) {
    return {
      columns: {
        per_100g: { ...EMPTY_COLUMN },
        per_serving: { ...EMPTY_COLUMN },
      },
      basis: "",
      category: "",
      serving: null,
    };
  }
  const w = draft.warnings;
  const mismatch = hasWarning(w, "basis_mismatch");
  const derived = draft.derived_from_serving;
  // R19: a derived draft's per_100g was computed by the server, not printed,
  // so it is never shown or sent as if it were printed.
  const per100 = derived ? column(null) : column(draft.per_100g);
  const perServing = draft.per_serving
    ? column(draft.per_serving)
    : mismatch && !derived
      ? column(draft.per_100g) // the printed numbers; their basis is in doubt
      : column(null);
  let basis: Basis | "" = "per_100g";
  if (mismatch) basis = "";
  else if (derived && draft.per_serving) basis = "per_serving";
  const categoryInDoubt =
    hasWarning(w, "category_unknown") || hasWarning(w, "category_check");
  return {
    columns: { per_100g: per100, per_serving: perServing },
    basis,
    category: categoryInDoubt ? "" : draft.category,
    serving: draft.serving_size_g,
  };
}

function needsClearAck(original: string | null | undefined, now: string) {
  return (original ?? "").trim() !== "" && now.trim() === "";
}

export function DraftForm({
  draft,
  onSave,
  scanId = null,
  barcode = null,
  busy = false,
  serverError = null,
}: {
  draft: ProductDraft | null;
  onSave(v: ProductCreate): void;
  /** The scan this draft came from; null for manual entry. */
  scanId?: string | null;
  barcode?: string | null;
  busy?: boolean;
  serverError?: ServerFieldError | null;
}) {
  const t = useTranslations();
  const uid = useId();
  const init = useMemo(() => initial(draft), [draft]);
  const isScan = draft !== null && scanId !== null;
  const warnings = draft?.warnings ?? [];
  const withheld = new Set<string>(draft?.engine_withheld ?? []);
  const derived = draft?.derived_from_serving ?? false;
  // basis_mismatch with one printed column: both bases show the same printed
  // numbers, so the user's edits follow the basis they pick.
  const oneColumn =
    draft !== null &&
    hasWarning(draft.warnings, "basis_mismatch") &&
    !derived &&
    !draft.per_serving;

  const [name, setName] = useState(draft?.name ?? "");
  const [brand, setBrand] = useState(draft?.brand ?? "");
  const [category, setCategory] = useState<Category | "">(init.category);
  const [basis, setBasis] = useState<Basis | "">(init.basis);
  const [sodiumUnit, setSodiumUnit] = useState<SodiumUnit | "">("");
  const [columns, setColumns] = useState(init.columns);
  const [serving, setServing] = useState<NumberInput>(init.serving);
  const [confirmed, setConfirmed] = useState<Set<ConfirmableField>>(
    () => new Set(),
  );
  const nextId = useRef(0);
  const [ingredients, setIngredients] = useState<Item[]>(() =>
    (draft?.ingredients ?? []).map((text) => ({ id: nextId.current++, text })),
  );
  const [allergen, setAllergen] = useState(draft?.allergen_statement ?? "");
  const [mayContain, setMayContain] = useState(
    draft?.may_contain_statement ?? "",
  );
  const [allergenAck, setAllergenAck] = useState(false);
  const [mayContainAck, setMayContainAck] = useState(false);
  const [claims, setClaims] = useState((draft?.claims ?? []).join("\n"));
  const [veg, setVeg] = useState<VegMark | "">(draft?.veg_mark ?? "");

  // Before a basis is chosen, show the column a derived draft printed.
  const shownBasis: Basis = basis || (derived ? "per_serving" : "per_100g");
  const values = columns[shownBasis];

  const sodiumNow = parseNumberInput(values.sodium_mg);
  // R19: any unit_unconfirmed sodium warning, on either column, needs a pick.
  const unitPicker =
    isScan && sodiumUnitUnconfirmed(warnings) && sodiumNow !== null;
  const servingShown =
    !isScan ||
    draft?.serving_size_g != null ||
    basis === "per_serving" ||
    derived;
  // R18/R19: per-serving values (or a derived draft) are stored only with a
  // confirmed serving size, so saving waits for the tick.
  const servingTickNeeded =
    isScan &&
    (derived || basis === "per_serving") &&
    !confirmed.has("serving_size_g");

  const highlights = highlightedFields(warnings);
  const serverFields = new Set(
    (serverError?.fields ?? [])
      .map(formFieldOf)
      .filter((f): f is string => f !== null),
  );
  for (const f of serverFields) highlights.add(f);

  const formValues: DraftFormValues = {
    scan_id: isScan ? scanId : null,
    barcode,
    name,
    brand,
    category,
    basis,
    sodium_unit: unitPicker ? sodiumUnit : "",
    nutrients: values,
    serving_size_g: serving,
    ingredients: ingredients.map((i) => i.text),
    allergen_statement: allergen,
    may_contain_statement: mayContain,
    claims: claims.split("\n"),
    veg_mark: veg,
    confirmed_fields: [...confirmed],
  };
  const parsed = draftSchema.safeParse(formValues);
  const invalidNumbers = new Set(
    parsed.success
      ? []
      : parsed.issues
          .filter((i) => i.code === "invalid_number")
          .map((i) => i.field),
  );
  const missing = {
    name: name.trim() === "",
    category: category === "",
    basis: basis === "",
    sodium_unit: unitPicker && sodiumUnit === "",
    serving_value:
      basis === "per_serving" && parseNumberInput(serving) === null,
    serving_tick: servingTickNeeded,
    allergen_ack:
      needsClearAck(draft?.allergen_statement, allergen) && !allergenAck,
    may_contain_ack:
      needsClearAck(draft?.may_contain_statement, mayContain) && !mayContainAck,
  };
  const blocked =
    busy || !parsed.success || Object.values(missing).some(Boolean);

  const confirm = (f: ConfirmableField, on: boolean) =>
    setConfirmed((prev) => {
      const next = new Set(prev);
      if (on) next.add(f);
      else next.delete(f);
      return next;
    });

  const chooseBasis = (b: Basis) => {
    if (oneColumn && b !== shownBasis)
      setColumns((prev) => ({ ...prev, [b]: prev[shownBasis] }));
    setBasis(b);
  };

  const editNutrient = (f: NutrientField, text: string) => {
    setColumns((prev) => ({
      ...prev,
      [shownBasis]: { ...prev[shownBasis], [f]: text },
    }));
    // Editing a withheld value is an explicit confirmation of it.
    if (isScan && withheld.has(f)) confirm(f as ConfirmableField, true);
  };

  const fieldError = (field: string): ReactNode =>
    serverFields.has(field) && serverError ? (
      <p role="alert" className="text-(length:--text-sm)">
        {t.has(`error.${serverError.code}`)
          ? t(`error.${serverError.code}`)
          : t("error.validation_error")}
      </p>
    ) : null;

  const chooseRequired = (
    <p className="text-(length:--text-sm) font-semibold">
      {t("confirm.choose_required")}
    </p>
  );

  const confirmBox = (f: ConfirmableField) => (
    <label className="flex items-center gap-(--spacing-2) text-(length:--text-sm)">
      <input
        type="checkbox"
        checked={confirmed.has(f)}
        onChange={(e) => confirm(f, e.target.checked)}
      />
      {t("confirm.confirm_value")}
    </label>
  );

  const rowClass = (field: string) =>
    `space-y-(--spacing-1) rounded-(--radius-sm) p-(--spacing-2) ${
      highlights.has(field) ? "border-2 border-(--color-verdict-caution)" : ""
    }`;
  const inputClass = "w-full border p-(--spacing-2) text-(length:--text-md)";

  const sodiumUnitText = unitPicker
    ? sodiumUnit
      ? t(`confirm.sodium_unit_option.${sodiumUnit}`)
      : `${t("confirm.sodium_unit_option.mg")} / ${t("confirm.sodium_unit_option.g")}`
    : t("confirm.sodium_unit_option.mg");

  return (
    <form
      className="space-y-(--spacing-4)"
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        if (!blocked && parsed.success) onSave(parsed.data);
      }}
    >
      <header className="space-y-(--spacing-1)">
        <h1 className="text-(length:--text-xl)">{t("confirm.title")}</h1>
        <p className="text-(length:--text-md)">{t("confirm.subtitle")}</p>
      </header>

      {warnings.length > 0 ? (
        <section className="space-y-(--spacing-2)">
          {warnings.map((w) => (
            <WarningBanner key={w} warning={w} />
          ))}
        </section>
      ) : null}

      <div data-testid="row-name" className={rowClass("name")}>
        <label htmlFor={`${uid}-name`} className="text-(length:--text-md)">
          {t("confirm.name")}
        </label>
        <input
          id={`${uid}-name`}
          type="text"
          value={name}
          maxLength={200}
          aria-invalid={serverFields.has("name") || undefined}
          onChange={(e) => setName(e.target.value)}
          className={inputClass}
        />
        {fieldError("name")}
      </div>

      <div data-testid="row-brand" className={rowClass("brand")}>
        <label htmlFor={`${uid}-brand`} className="text-(length:--text-md)">
          {t("confirm.brand")}
        </label>
        <input
          id={`${uid}-brand`}
          type="text"
          value={brand}
          maxLength={200}
          onChange={(e) => setBrand(e.target.value)}
          className={inputClass}
        />
        {fieldError("brand")}
      </div>

      <fieldset data-testid="choice-category" className={rowClass("category")}>
        <legend className="text-(length:--text-md)">
          {t("confirm.category")}
        </legend>
        <div className="flex flex-wrap gap-(--spacing-3)">
          {CATEGORIES.map((c) => (
            <label key={c} className="flex items-center gap-(--spacing-1)">
              <input
                type="radio"
                name="category"
                value={c}
                checked={category === c}
                onChange={() => setCategory(c)}
              />
              {t(`confirm.category_option.${c}`)}
            </label>
          ))}
        </div>
        {missing.category ? chooseRequired : null}
        {fieldError("category")}
      </fieldset>

      <fieldset data-testid="choice-basis" className={rowClass("basis")}>
        <legend className="text-(length:--text-md)">
          {t("confirm.basis")}
        </legend>
        <div className="flex flex-wrap gap-(--spacing-3)">
          {BASES.map((b) => (
            <label key={b} className="flex items-center gap-(--spacing-1)">
              <input
                type="radio"
                name="basis"
                value={b}
                checked={basis === b}
                onChange={() => chooseBasis(b)}
              />
              {t(`confirm.basis_option.${b}`)}
            </label>
          ))}
        </div>
        {missing.basis ? chooseRequired : null}
        {fieldError("basis")}
      </fieldset>

      {servingShown ? (
        <div
          data-testid="row-serving_size_g"
          data-highlight={highlights.has("serving_size_g") ? "true" : "false"}
          className={rowClass("serving_size_g")}
        >
          <label htmlFor={`${uid}-serving`} className="text-(length:--text-md)">
            {t("confirm.serving_size")}
          </label>
          <input
            id={`${uid}-serving`}
            type="text"
            inputMode="decimal"
            autoComplete="off"
            value={shown(serving)}
            aria-invalid={
              invalidNumbers.has("serving_size_g") ||
              serverFields.has("serving_size_g") ||
              missing.serving_value ||
              undefined
            }
            onChange={(e) => {
              setServing(e.target.value);
              // Editing the serving size confirms it (R18).
              if (isScan) confirm("serving_size_g", true);
            }}
            className={inputClass}
          />
          {isScan ? confirmBox("serving_size_g") : null}
          {missing.serving_value || missing.serving_tick
            ? chooseRequired
            : null}
          {invalidNumbers.has("serving_size_g") ? (
            <p role="alert" className="text-(length:--text-sm)">
              {t("error.validation_error")}
            </p>
          ) : null}
          {fieldError("serving_size_g")}
        </div>
      ) : null}

      {unitPicker ? (
        <fieldset
          data-testid="choice-sodium_unit"
          className={rowClass("sodium_unit")}
        >
          <legend className="text-(length:--text-md)">
            {t("confirm.sodium_unit")}
          </legend>
          <div className="flex flex-wrap gap-(--spacing-3)">
            {SODIUM_UNITS.map((u) => (
              <label key={u} className="flex items-center gap-(--spacing-1)">
                <input
                  type="radio"
                  name="sodium_unit"
                  value={u}
                  checked={sodiumUnit === u}
                  onChange={() => setSodiumUnit(u)}
                />
                {t(`confirm.sodium_unit_option.${u}`)}
              </label>
            ))}
          </div>
          {missing.sodium_unit ? chooseRequired : null}
          {fieldError("sodium_unit")}
        </fieldset>
      ) : null}

      <section className="space-y-(--spacing-2)">
        <p className="text-(length:--text-sm)">
          {t("confirm.leave_blank_hint")}
        </p>
        {derived ? (
          <p className="text-(length:--text-md) font-semibold">
            {t("confirm.derived_per_serving", { serving: shown(serving) })}
          </p>
        ) : null}
        {NUTRIENT_FIELDS.map((f) => {
          const id = `${uid}-${f}`;
          const isSodium = f === "sodium_mg";
          const label =
            isSodium && unitPicker
              ? t("confirm.sodium")
              : t(`confirm.field.${f}`);
          const invalid = invalidNumbers.has(f) || serverFields.has(f);
          return (
            <div
              key={f}
              data-testid={`row-${f}`}
              data-highlight={highlights.has(f) ? "true" : "false"}
              className={rowClass(f)}
            >
              <label htmlFor={id} className="text-(length:--text-md)">
                {label}
              </label>
              <div className="flex items-center gap-(--spacing-2)">
                <input
                  id={id}
                  type="text"
                  inputMode="decimal"
                  autoComplete="off"
                  value={shown(values[f])}
                  aria-invalid={invalid || undefined}
                  onChange={(e) => editNutrient(f, e.target.value)}
                  className={inputClass}
                />
                {isSodium ? (
                  <span
                    data-testid="sodium-unit"
                    className="text-(length:--text-md)"
                  >
                    {sodiumUnitText}
                  </span>
                ) : null}
              </div>
              {isScan && withheld.has(f) ? (
                <>
                  <p className="text-(length:--text-sm)">
                    {t("confirm.withheld_hint")}
                  </p>
                  {confirmBox(f as ConfirmableField)}
                </>
              ) : null}
              {invalidNumbers.has(f) && !serverFields.has(f) ? (
                <p role="alert" className="text-(length:--text-sm)">
                  {t("error.validation_error")}
                </p>
              ) : null}
              {fieldError(f)}
            </div>
          );
        })}
      </section>

      <section
        data-testid="row-ingredients"
        className={`${rowClass("ingredients")} space-y-(--spacing-2)`}
      >
        <h2 className="text-(length:--text-md)">{t("confirm.ingredients")}</h2>
        <ul className="space-y-(--spacing-2)">
          {ingredients.map((item, i) => (
            <li key={item.id} className="flex gap-(--spacing-2)">
              <input
                type="text"
                aria-label={`${t("confirm.ingredients")} ${i + 1}`}
                value={item.text}
                maxLength={1000}
                onChange={(e) =>
                  setIngredients((prev) =>
                    prev.map((p) =>
                      p.id === item.id ? { ...p, text: e.target.value } : p,
                    ),
                  )
                }
                className={inputClass}
              />
              <button
                type="button"
                onClick={() =>
                  setIngredients((prev) => prev.filter((p) => p.id !== item.id))
                }
                className="rounded-(--radius-md) border px-(--spacing-2) text-(length:--text-sm)"
              >
                {t("confirm.remove_ingredient")}
              </button>
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={() =>
            setIngredients((prev) => [
              ...prev,
              { id: nextId.current++, text: "" },
            ])
          }
          className="rounded-(--radius-md) border px-(--spacing-3) py-(--spacing-1) text-(length:--text-md)"
        >
          {t("confirm.add_ingredient")}
        </button>
        {fieldError("ingredients")}
      </section>

      <Statement
        id={`${uid}-allergen`}
        field="allergen_statement"
        label={t("confirm.allergen_statement")}
        value={allergen}
        onChange={(v) => {
          setAllergen(v);
          setAllergenAck(false);
        }}
        needsAck={needsClearAck(draft?.allergen_statement, allergen)}
        ack={allergenAck}
        onAck={setAllergenAck}
        ackLabel={t("confirm.clear_statement_confirm")}
        highlighted={highlights.has("allergen_statement")}
        error={fieldError("allergen_statement")}
      />
      <Statement
        id={`${uid}-may`}
        field="may_contain_statement"
        label={t("confirm.may_contain_statement")}
        value={mayContain}
        onChange={(v) => {
          setMayContain(v);
          setMayContainAck(false);
        }}
        needsAck={needsClearAck(draft?.may_contain_statement, mayContain)}
        ack={mayContainAck}
        onAck={setMayContainAck}
        ackLabel={t("confirm.clear_statement_confirm")}
        highlighted={highlights.has("may_contain_statement")}
        error={fieldError("may_contain_statement")}
      />

      <div data-testid="row-claims" className={rowClass("claims")}>
        <label htmlFor={`${uid}-claims`} className="text-(length:--text-md)">
          {t("confirm.claims")}
        </label>
        <textarea
          id={`${uid}-claims`}
          rows={3}
          value={claims}
          onChange={(e) => setClaims(e.target.value)}
          className={inputClass}
        />
        {fieldError("claims")}
      </div>

      <fieldset data-testid="choice-veg_mark" className={rowClass("veg_mark")}>
        <legend className="text-(length:--text-md)">
          {t("confirm.veg_mark_title")}
        </legend>
        <div className="flex flex-wrap gap-(--spacing-3)">
          {(["veg", "non_veg", ""] as const).map((v) => (
            <label
              key={v || "none"}
              className="flex items-center gap-(--spacing-1)"
            >
              <input
                type="radio"
                name="veg_mark"
                value={v || "none"}
                checked={veg === v}
                onChange={() => setVeg(v)}
              />
              {t(`confirm.veg_mark.${v || "none"}`)}
            </label>
          ))}
        </div>
        {fieldError("veg_mark")}
      </fieldset>

      <p className="text-(length:--text-sm)">
        {t("confirm.not_medical_advice")}
      </p>

      <button
        type="submit"
        disabled={blocked}
        className="w-full rounded-(--radius-md) border px-(--spacing-4) py-(--spacing-2) text-(length:--text-md) disabled:opacity-50"
      >
        {busy ? t("common.loading") : t("confirm.save")}
      </button>
    </form>
  );
}

/** An allergen text, shown in full and editable; blanking it needs a tick. */
function Statement(props: {
  id: string;
  field: string;
  label: string;
  value: string;
  onChange(v: string): void;
  needsAck: boolean;
  ack: boolean;
  onAck(v: boolean): void;
  ackLabel: string;
  highlighted: boolean;
  error: ReactNode;
}) {
  return (
    <div
      data-testid={`row-${props.field}`}
      className={`space-y-(--spacing-1) rounded-(--radius-sm) p-(--spacing-2) ${
        props.highlighted ? "border-2 border-(--color-verdict-caution)" : ""
      }`}
    >
      <label htmlFor={props.id} className="text-(length:--text-md)">
        {props.label}
      </label>
      <textarea
        id={props.id}
        rows={3}
        maxLength={4000}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        className="w-full border p-(--spacing-2) text-(length:--text-md)"
      />
      {props.needsAck ? (
        <label className="flex items-center gap-(--spacing-2) border-2 border-(--color-verdict-caution) p-(--spacing-2) text-(length:--text-sm)">
          <input
            type="checkbox"
            checked={props.ack}
            onChange={(e) => props.onAck(e.target.checked)}
          />
          {props.ackLabel}
        </label>
      ) : null}
      {props.error}
    </div>
  );
}
