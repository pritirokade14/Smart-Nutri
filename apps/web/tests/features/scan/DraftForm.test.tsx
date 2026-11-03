import messages from "@smartnutri/i18n/messages/en.json";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DraftForm } from "@/features/scan/components/DraftForm";
import {
  ENGINE_FIELDS,
  type ProductCreate,
  type ProductDraft,
} from "@/features/scan/lib/draftSchema";
import {
  type DraftCase,
  draft as fixture,
  SCAN_ID,
} from "../../support/drafts";

// UI-only behaviour. The bodies for every scripted save of the shared drafts
// are asserted in draftFixtures.test.tsx.

const c = messages.confirm;

afterEach(cleanup);

function setup(
  name: DraftCase | ProductDraft | null,
  barcode: string | null = null,
) {
  const onSave = vi.fn<(v: ProductCreate) => void>();
  const draft = typeof name === "string" ? fixture(name) : name;
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <DraftForm
        draft={draft}
        scanId={draft ? SCAN_ID : null}
        barcode={barcode}
        onSave={onSave}
      />
    </NextIntlClientProvider>,
  );
  return { onSave, draft };
}

const user = () => userEvent.setup();
const save = () => screen.getByRole("button", { name: c.save });
const row = (field: string) => screen.getByTestId(`row-${field}`);
const input = (field: string) =>
  within(row(field)).getByRole("textbox") as HTMLInputElement;
const confirmBox = (field: string) =>
  within(row(field)).getByRole("checkbox", { name: c.confirm_value });
const basisRadio = (b: "per_100g" | "per_serving") =>
  screen.getByRole("radio", { name: c.basis_option[b] }) as HTMLInputElement;

async function saved(onSave: ReturnType<typeof setup>["onSave"]) {
  await user().click(save());
  expect(onSave).toHaveBeenCalledTimes(1);
  return onSave.mock.calls[0]?.[0] as ProductCreate;
}

describe("DraftForm: prefill and blanks", () => {
  it("shows the draft as printed and sends the scan id and barcode", async () => {
    const { onSave } = setup("clean", "8901063201089");
    expect(input("sugars_g").value).toBe("10");
    expect(input("trans_fat_g").value).toBe("0.1");
    expect(screen.getByText(c.not_medical_advice)).toBeTruthy();
    const body = await saved(onSave);
    expect(body.scan_id).toBe(SCAN_ID);
    expect(body.barcode).toBe("8901063201089");
  });

  it("a cleared field is sent as null, never 0", async () => {
    const { onSave } = setup("category_check");
    await user().click(
      screen.getByRole("radio", { name: c.category_option.beverage }),
    );
    expect(input("fiber_g").value).toBe(""); // draft blank stays blank
    await user().clear(input("sugars_g"));
    const body = await saved(onSave);
    expect(body.nutrients.sugars_g).toBeNull();
    expect(body.nutrients.fiber_g).toBeNull();
  });

  it("Enter manually: an empty form, nothing preselected, no scan id, no boxes", async () => {
    const { onSave } = setup(null, "8901063201089");
    for (const f of ["energy_kcal", "sugars_g", "sodium_mg", "serving_size_g"])
      expect(input(f).value).toBe("");
    expect((screen.getByLabelText(c.name) as HTMLInputElement).value).toBe("");
    for (const r of screen.queryAllByRole("radio") as HTMLInputElement[]) {
      if (r.name !== "veg_mark") expect(r.checked).toBe(false);
      expect(r.disabled).toBe(false);
    }
    expect(screen.queryAllByTestId(/^confirm-/)).toHaveLength(0);
    expect(save()).toHaveProperty("disabled", true);
    await user().type(screen.getByLabelText(c.name), "Home Chivda");
    await user().click(
      screen.getByRole("radio", { name: c.category_option.general }),
    );
    await user().click(basisRadio("per_100g"));
    await user().type(input("sugars_g"), "12.5");
    await user().type(input("serving_size_g"), "25");
    const body = await saved(onSave);
    expect("scan_id" in body).toBe(false);
    expect(body.barcode).toBe("8901063201089");
    expect(body.nutrients.sugars_g).toBe(12.5);
    expect(body.nutrients.energy_kcal).toBeNull();
    expect(body.sodium_unit).toBeNull();
    expect(body.confirmed_fields).toEqual([]);
  });

  it("manual per_serving needs a serving size", async () => {
    setup(null);
    await user().type(screen.getByLabelText(c.name), "Home Chivda");
    await user().click(
      screen.getByRole("radio", { name: c.category_option.general }),
    );
    await user().click(basisRadio("per_serving"));
    expect(save()).toHaveProperty("disabled", true);
    await user().type(input("serving_size_g"), "25");
    expect(save()).toHaveProperty("disabled", false);
  });
});

describe("DraftForm: confirm boxes come only from draft.confirm", () => {
  it("upper_bound protein: unticked box with the hint; editing the value confirms it", async () => {
    const { onSave } = setup("upper_bound_protein_per_100g");
    expect(within(row("protein_g")).getByText(c.withheld_hint)).toBeTruthy();
    expect(confirmBox("protein_g")).toHaveProperty("checked", false);
    await user().clear(input("protein_g"));
    await user().type(input("protein_g"), "0.4");
    const body = await saved(onSave);
    expect(body.nutrients.protein_g).toBe(0.4);
    expect(body.confirmed_fields).toEqual(["protein_g"]);
  });

  it("upper_bound on the per-serving column still asks on the per-100 g save", () => {
    setup("upper_bound_protein_per_serving");
    expect(basisRadio("per_100g").checked).toBe(true);
    expect(confirmBox("protein_g")).toHaveProperty("checked", false);
    expect(confirmBox("serving_size_g")).toHaveProperty("checked", false);
  });

  it("basis_mismatch: never nine boxes, only the column's confirm_fields", async () => {
    setup("basis_mismatch_both_columns");
    await user().click(basisRadio("per_100g"));
    expect(
      screen.queryAllByTestId(/^confirm-/).map((e) => e.dataset.testid),
    ).toEqual(["confirm-serving_size_g"]);
    for (const f of ENGINE_FIELDS)
      expect(within(row(f)).queryByRole("checkbox")).toBeNull();
    expect(screen.queryByText(c.withheld_hint)).toBeNull();
  });

  it("an edited value that the hint doesn't list is not sent as confirmed", async () => {
    const { onSave } = setup("clean");
    await user().clear(input("sugars_g"));
    await user().type(input("sugars_g"), "9");
    expect((await saved(onSave)).confirmed_fields).toEqual([]);
  });

  it("a tick on one printed column never confirms the other column's value", async () => {
    // A synthetic hint asking for protein on both printed columns.
    const d = fixture("basis_mismatch_both_columns");
    const col = {
      printed: true,
      shared: false,
      sodium_unit_required: false,
      confirm_fields: ["protein_g" as const, "serving_size_g" as const],
    };
    const draft: ProductDraft = {
      ...d,
      confirm: { ...d.confirm, columns: { per_100g: col, per_serving: col } },
    };
    const { onSave } = setup(draft);
    await user().click(basisRadio("per_100g"));
    await user().click(confirmBox("protein_g"));
    await user().click(basisRadio("per_serving"));
    expect(confirmBox("protein_g")).toHaveProperty("checked", false);
    await user().click(confirmBox("serving_size_g"));
    const body = await saved(onSave);
    expect(body.confirmed_fields).toEqual(["serving_size_g"]);
  });
});

describe("DraftForm: warnings", () => {
  it("a code:path warning renders warning.<code>, the field label, and highlights the field", () => {
    setup("upper_bound_protein_per_100g");
    const banner = screen.getByTestId("warning-upper_bound:per_100g.protein_g");
    expect(within(banner).getByText(messages.warning.upper_bound)).toBeTruthy();
    expect(within(banner).getByText(c.field.protein_g)).toBeTruthy();
    expect(row("protein_g").getAttribute("data-highlight")).toBe("true");
    expect(row("sugars_g").getAttribute("data-highlight")).toBe("false");
  });

  it("highlights implausible fields and shows the warning", () => {
    setup("implausible_value");
    const banner = screen.getByTestId("warning-implausible_value:sugars_g");
    expect(
      within(banner).getByText(messages.warning.implausible_value),
    ).toBeTruthy();
    expect(within(banner).getByText(c.field.sugars_g)).toBeTruthy();
    expect(row("sugars_g").getAttribute("data-highlight")).toBe("true");
    expect(input("sugars_g").value).toBe("40");
  });

  it("low_confidence is prominent (an alert) and never green", () => {
    setup("low_confidence");
    const banner = screen.getByTestId("warning-low_confidence");
    expect(banner.getAttribute("role")).toBe("alert");
    expect(banner.className).not.toMatch(/verdict-ok/);
  });
});

describe("DraftForm: forced choices", () => {
  it("basis_required: both offered, none preselected, choose_required shown", () => {
    setup("basis_mismatch_both_columns");
    for (const b of ["per_100g", "per_serving"] as const) {
      expect(basisRadio(b).checked).toBe(false);
      expect(basisRadio(b).disabled).toBe(false);
    }
    expect(save()).toHaveProperty("disabled", true);
    expect(
      within(screen.getByTestId("choice-basis")).getByText(c.choose_required),
    ).toBeTruthy();
  });

  it("shared column: edits made before choosing the basis are kept, and the chosen basis is labelled", async () => {
    const { onSave } = setup("basis_mismatch_one_column");
    expect(screen.queryByTestId("shared-basis")).toBeNull();
    await user().clear(input("sugars_g"));
    await user().type(input("sugars_g"), "5.5");
    await user().click(basisRadio("per_serving"));
    expect(input("sugars_g").value).toBe("5.5");
    expect(screen.getByTestId("shared-basis").textContent).toBe(
      c.basis_option.per_serving,
    );
    await user().click(basisRadio("per_100g"));
    expect(input("sugars_g").value).toBe("5.5");
    expect(screen.getByTestId("shared-basis").textContent).toBe(
      c.basis_option.per_100g,
    );
    await user().click(confirmBox("serving_size_g"));
    expect((await saved(onSave)).nutrients.sugars_g).toBe(5.5);
  });

  it("two printed columns: each basis shows its own column, no shared label", async () => {
    setup("basis_mismatch_both_columns");
    await user().click(basisRadio("per_serving"));
    expect(input("sugars_g").value).toBe("3");
    expect(screen.queryByTestId("shared-basis")).toBeNull();
    await user().click(basisRadio("per_100g"));
    expect(input("sugars_g").value).toBe("10");
  });

  it("sodium unit: 'Sodium' label, unit beside the input, save waits for the pick", async () => {
    setup("unit_unconfirmed_sodium_per_100g");
    expect(within(row("sodium_mg")).getByText(c.sodium)).toBeTruthy();
    expect(within(row("sodium_mg")).queryByText(c.field.sodium_mg)).toBeNull();
    expect(
      within(row("sodium_mg")).getByTestId("sodium-unit").textContent,
    ).toBe(`${c.sodium_unit_option.mg} / ${c.sodium_unit_option.g}`);
    expect(within(row("sodium_mg")).queryByRole("checkbox")).toBeNull();
    expect(save()).toHaveProperty("disabled", true);
    await user().click(screen.getByRole("radio", { name: "g" }));
    expect(
      within(row("sodium_mg")).getByTestId("sodium-unit").textContent,
    ).toBe(c.sodium_unit_option.g);
    expect(save()).toHaveProperty("disabled", false);
  });

  it("sodium unit: a blank sodium needs no pick", async () => {
    const { onSave } = setup("unit_unconfirmed_sodium_per_100g");
    await user().clear(input("sodium_mg"));
    expect(screen.queryByTestId("choice-sodium_unit")).toBeNull();
    const body = await saved(onSave);
    expect(body.nutrients.sodium_mg).toBeNull();
    expect(body.sodium_unit).toBeNull();
  });

  it("no unit hint: no picker, sodium labelled in mg once, no extra suffix", () => {
    setup("clean");
    expect(screen.queryByTestId("choice-sodium_unit")).toBeNull();
    expect(within(row("sodium_mg")).getByText(c.field.sodium_mg)).toBeTruthy();
    expect(within(row("sodium_mg")).queryByTestId("sodium-unit")).toBeNull();
  });

  it("category_required: nothing preselected until the user picks", () => {
    setup("category_unknown");
    for (const r of screen.getAllByRole("radio", {
      name: (n) => (Object.values(c.category_option) as string[]).includes(n),
    }))
      expect(r).toHaveProperty("checked", false);
    expect(
      within(screen.getByTestId("choice-category")).getByText(
        c.choose_required,
      ),
    ).toBeTruthy();
  });
});

describe("DraftForm: serving size (R18/R21)", () => {
  it("typing a serving where the draft had none confirms it", async () => {
    const { onSave } = setup("clean");
    expect(input("serving_size_g").value).toBe("");
    expect(within(row("serving_size_g")).queryByRole("checkbox")).toBeNull();
    await user().type(input("serving_size_g"), "30");
    const body = await saved(onSave);
    expect(body.serving_size_g).toBe(30);
    expect(body.confirmed_fields).toEqual(["serving_size_g"]);
  });

  it("editing a listed serving confirms it", async () => {
    const { onSave } = setup("upper_bound_protein_per_serving");
    await user().clear(input("serving_size_g"));
    await user().type(input("serving_size_g"), "25");
    const body = await saved(onSave);
    expect(body.serving_size_g).toBe(25);
    expect(body.confirmed_fields).toEqual(["serving_size_g"]);
  });

  it("only per_serving offered: it is selected, per_100g is disabled, the printed column shows", async () => {
    setup("derived_from_serving");
    expect(basisRadio("per_serving").checked).toBe(true);
    expect(basisRadio("per_100g").disabled).toBe(true);
    expect(input("sugars_g").value).toBe("3"); // printed, not the derived 10
    expect(input("serving_size_g").value).toBe("30");
    expect(
      screen.getByText(c.derived_per_serving.replace("{serving}", "30")),
    ).toBeTruthy();
    expect(save()).toHaveProperty("disabled", true);
    await user().clear(input("serving_size_g"));
    await user().type(input("serving_size_g"), "35");
    expect(
      screen.getByText(c.derived_per_serving.replace("{serving}", "35")),
    ).toBeTruthy();
    expect(save()).toHaveProperty("disabled", false);
  });

  it("never shows the server-derived per_100g as printed", async () => {
    setup("derived_basis_mismatch");
    await user().click(basisRadio("per_100g"));
    expect(input("sugars_g").value).toBe("3"); // the shared printed column
    expect(input("energy_kcal").value).toBe("45"); // not the derived 150
  });
});

describe("DraftForm: allergens and ingredients", () => {
  it("Devanagari ingredients round-trip unchanged into the body", async () => {
    const { onSave, draft } = setup("devanagari");
    expect(screen.getByDisplayValue("बेसन")).toBeTruthy();
    expect(screen.getByDisplayValue("इसमें मूंगफली है")).toBeTruthy();
    const body = await saved(onSave);
    expect(body.ingredients).toEqual(draft?.ingredients);
    expect(body.allergen_statement).toBe(draft?.allergen_statement);
    expect(body.name).toBe("नमकीन मिक्सचर");
  });

  it("ingredients can be added and removed by the user", async () => {
    const { onSave } = setup("clean");
    await user().click(screen.getByRole("button", { name: c.add_ingredient }));
    const items = screen.getAllByRole("textbox", {
      name: new RegExp(`^${c.ingredients} \\d+$`),
    });
    await user().type(items.at(-1) as HTMLElement, "मिर्च");
    await user().click(
      screen.getAllByRole("button", {
        name: c.remove_ingredient,
      })[0] as HTMLElement,
    );
    expect((await saved(onSave)).ingredients).toEqual([
      "edible vegetable oil (palm)",
      "sugar",
      "salt",
      "मिर्च",
    ]);
  });

  it("clearing the allergen statement needs a deliberate confirmation", async () => {
    const { onSave } = setup("clean");
    await user().clear(screen.getByLabelText(c.allergen_statement));
    expect(save()).toHaveProperty("disabled", true);
    await user().click(
      screen.getByRole("checkbox", { name: c.clear_statement_confirm }),
    );
    const body = await saved(onSave);
    expect(body.allergen_statement).toBeNull();
    expect(body.may_contain_statement).toBe("May contain milk");
  });

  it("clearing the may-contain statement needs a deliberate confirmation", async () => {
    setup("clean");
    await user().clear(screen.getByLabelText(c.may_contain_statement));
    expect(save()).toHaveProperty("disabled", true);
    expect(
      screen.getByRole("checkbox", { name: c.clear_statement_confirm }),
    ).toBeTruthy();
  });
});
