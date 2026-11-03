"use client";

import { useTranslations } from "next-intl";
import { type ReactNode, useId, useMemo, useRef, useState } from "react";
import {
  BASES,
  type Basis,
  CATEGORIES,
  type Category,
  CONFIRMABLE_FIELDS,
  type ColumnConfirm,
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
import { highlightedFields } from "../lib/warnings";
import { WarningBanner } from "./WarningBanner";

export type ServerFieldError = { code: string; fields: string[] };

type Column = Record<NutrientField, NumberInput>;
type Columns = Record<Basis, Column>;
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

/**
 * The form's reading of `draft.confirm` (Ruling R21). Nothing here looks at
 * `warnings`, `engine_withheld`, `derived_from_serving` or `basis_mismatch`:
 * the server computes the hints with the same helpers that enforce the save.
 */
type Hints = {
  /** Bases the user may save with: the non-null `confirm.columns`. */
  offered: readonly Basis[];
  /** Per basis: the draft column whose printed values it shows. */
  source: Record<Basis, Basis>;
  /** Per basis: what to ask on save; null for manual entry or not offered. */
  column: Record<Basis, ColumnConfirm | null>;
  /** The column shown before the user picks a basis. */
  fallback: Basis;
  basis: Basis | "";
  category: Category | "";
  values: Columns;
};

function hintsOf(draft: ProductDraft | null): Hints {
  if (!draft) {
    // Manual entry: an empty form, both bases offered, nothing preselected.
    return {
      offered: BASES,
      source: { per_100g: "per_100g", per_serving: "per_serving" },
      column: { per_100g: null, per_serving: null },
      fallback: "per_100g",
      basis: "",
      category: "",
      values: {
        per_100g: { ...EMPTY_COLUMN },
        per_serving: { ...EMPTY_COLUMN },
      },
    };
  }
  const { basis_required, category_required, columns: cols } = draft.confirm;
  const offered = BASES.filter((b) => cols[b] !== null);
  const shared = BASES.find((b) => cols[b]?.shared) ?? null;
  const printed = BASES.filter((b) => cols[b]?.printed);
  // Only a column the server marks printed is shown as printed: the
  // server-derived per_100g of a per-serving label never is.
  const draftColumn = (b: Basis) =>
    b === "per_100g" ? draft.per_100g : draft.per_serving;
  const values = {
    per_100g: cols.per_100g?.printed
      ? column(draftColumn("per_100g"))
      : column(null),
    per_serving: cols.per_serving?.printed
      ? column(draftColumn("per_serving"))
      : column(null),
  };
  const sourceOf = (b: Basis): Basis => (cols[b]?.printed ? b : (shared ?? b));
  // R22: with the basis not in doubt, the only offered column, or per_100g
  // when both are offered (the user can switch). In doubt: nothing.
  const preselect: Basis | "" = basis_required
    ? ""
    : offered.length > 1 && offered.includes("per_100g")
      ? "per_100g"
      : (offered[0] ?? "");
  return {
    offered,
    source: {
      per_100g: sourceOf("per_100g"),
      per_serving: sourceOf("per_serving"),
    },
    column: { per_100g: cols.per_100g, per_serving: cols.per_serving },
    fallback: shared ?? printed[0] ?? offered[0] ?? "per_100g",
    basis: preselect,
    category: category_required ? "" : draft.category,
    values,
  };
}

function needsClearAck(original: string | null | undefined, now: string) {
  return (original ?? "").trim() !== "" && now.trim() === "";
}

export function DraftForm({
  scan,
  onSave,
  barcode = null,
  busy = false,
  serverError = null,
}: {
  /** The scan and its draft; null for manual entry (R24: one prop, so a draft is never sent as manual entry). */
  scan: { scanId: string; draft: ProductDraft } | null;
  onSave(v: ProductCreate): void;
  barcode?: string | null;
  busy?: boolean;
  serverError?: ServerFieldError | null;
}) {
  const t = useTranslations();
  const uid = useId();
  const draft = scan?.draft ?? null;
  const scanId = scan?.scanId ?? null;
  const hints = useMemo(() => hintsOf(draft), [draft]);
  const isScan = scan !== null;
  const warnings = draft?.warnings ?? [];

  const [name, setName] = useState(draft?.name ?? "");
  const [brand, setBrand] = useState(draft?.brand ?? "");
  const [category, setCategory] = useState<Category | "">(hints.category);
  const [basis, setBasis] = useState<Basis | "">(hints.basis);
  const [sodiumUnit, setSodiumUnit] = useState<SodiumUnit | "">("");
  const [columns, setColumns] = useState<Columns>(hints.values);
  const [serving, setServing] = useState<NumberInput>(
    draft?.serving_size_g ?? null,
  );
  // Ticks, keyed by the printed column whose value they confirm
  // ("per_100g.protein_g"), or "serving_size_g" for the serving size.
  const [ticked, setTicked] = useState<ReadonlySet<string>>(() => new Set());
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

  const shownBasis: Basis = basis || hints.fallback;
  const source = hints.source[shownBasis];
  const values = columns[source];
  // R24: no confirm boxes (and no confirmations) until a basis is chosen.
  const hint = isScan && basis !== "" ? hints.column[basis] : null;
  const sharedShown = isScan && (hints.column[source]?.shared ?? false);
  const boxes = new Set<ConfirmableField>(hint?.confirm_fields ?? []);
  const keyOf = (f: ConfirmableField) =>
    f === "serving_size_g" ? f : `${source}.${f}`;
  // R24: confirmed = ticked, or the current value differs from the value the
  // draft shows. Editing back to the draft's value confirms nothing.
  const changed = (f: ConfirmableField): boolean => {
    if (f === "serving_size_g")
      return parseNumberInput(serving) !== (draft?.serving_size_g ?? null);
    // Unparseable text is undefined, so it differs from any printed value.
    return (
      parseNumberInput(values[f]) !== parseNumberInput(hints.values[source][f])
    );
  };
  const confirmedFields = isScan
    ? CONFIRMABLE_FIELDS.filter(
        (f) =>
          (boxes.has(f) && (ticked.has(keyOf(f)) || changed(f))) ||
          // A serving size the user typed or changed is theirs (R18/R21),
          // even where the draft had none and the hint lists no box for it.
          (f === "serving_size_g" && changed(f)),
      )
    : [];

  const sodiumNow = parseNumberInput(values.sodium_mg);
  const unitPicker =
    (hint?.sodium_unit_required ?? false) && sodiumNow !== null;
  // The server says when nutrients are stored only with a confirmed serving
  // (R23); without it every nutrient would be saved as null.
  const servingTickNeeded =
    basis !== "" &&
    (hint?.serving_required ?? false) &&
    !confirmedFields.includes("serving_size_g");

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
    confirmed_fields: confirmedFields,
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

  const tick = (f: ConfirmableField, on: boolean) =>
    setTicked((prev) => {
      const next = new Set(prev);
      if (on) next.add(keyOf(f));
      else next.delete(keyOf(f));
      return next;
    });

  const editNutrient = (f: NutrientField, text: string) => {
    setColumns((prev) => ({
      ...prev,
      [source]: { ...prev[source], [f]: text },
    }));
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

  // Unticked by default; never pre-ticked.
  const confirmBox = (f: ConfirmableField) => (
    <label className="flex items-center gap-(--spacing-2) text-(length:--text-sm)">
      <input
        type="checkbox"
        data-testid={`confirm-${f}`}
        checked={ticked.has(keyOf(f))}
        onChange={(e) => tick(f, e.target.checked)}
      />
      {t("confirm.confirm_value")}
    </label>
  );

  const rowClass = (field: string) =>
    `space-y-(--spacing-1) rounded-(--radius-sm) p-(--spacing-2) ${
      highlights.has(field) ? "border-2 border-(--color-verdict-caution)" : ""
    }`;
  const inputClass = "w-full border p-(--spacing-2) text-(length:--text-md)";

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
          {BASES.map((b) => {
            const off = !hints.offered.includes(b);
            return (
              <label
                key={b}
                className={`flex items-center gap-(--spacing-1) ${off ? "opacity-50" : ""}`}
              >
                <input
                  type="radio"
                  name="basis"
                  value={b}
                  checked={basis === b}
                  disabled={off}
                  onChange={() => {
                    if (b !== basis) setSodiumUnit(""); // R24: new column, new unit
                    setBasis(b);
                  }}
                />
                {t(`confirm.basis_option.${b}`)}
              </label>
            );
          })}
        </div>
        {missing.basis ? chooseRequired : null}
        {fieldError("basis")}
      </fieldset>

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
          }}
          className={inputClass}
        />
        {boxes.has("serving_size_g") ? confirmBox("serving_size_g") : null}
        {missing.serving_value || missing.serving_tick ? chooseRequired : null}
        {invalidNumbers.has("serving_size_g") ? (
          <p role="alert" className="text-(length:--text-sm)">
            {t("error.validation_error")}
          </p>
        ) : null}
        {fieldError("serving_size_g")}
      </div>

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
        {sharedShown && basis ? (
          // One printed column whose basis is the doubt: say which basis
          // these numbers will be saved as.
          <p
            data-testid="shared-basis"
            className="text-(length:--text-md) font-semibold"
          >
            {t(`confirm.basis_option.${basis}`)}
          </p>
        ) : null}
        {draft?.derived_from_serving ? (
          <p className="text-(length:--text-md) font-semibold">
            {t("confirm.derived_per_serving", { serving: shown(serving) })}
          </p>
        ) : null}
        {NUTRIENT_FIELDS.map((f) => {
          const id = `${uid}-${f}`;
          const isSodium = f === "sodium_mg";
          // The picker's unit sits beside the input; otherwise the label
          // already says "(mg)".
          const label =
            isSodium && unitPicker
              ? t("confirm.sodium")
              : t(`confirm.field.${f}`);
          const invalid = invalidNumbers.has(f) || serverFields.has(f);
          const box = boxes.has(f as ConfirmableField);
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
                {isSodium && unitPicker ? (
                  <span
                    data-testid="sodium-unit"
                    className="text-(length:--text-md)"
                  >
                    {sodiumUnit
                      ? t(`confirm.sodium_unit_option.${sodiumUnit}`)
                      : `${t("confirm.sodium_unit_option.mg")} / ${t("confirm.sodium_unit_option.g")}`}
                  </span>
                ) : null}
              </div>
              {box ? (
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
