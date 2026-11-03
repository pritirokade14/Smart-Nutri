import messages from "@smartnutri/i18n/messages/en.json";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DraftForm } from "@/features/scan/components/DraftForm";
import {
  ENGINE_FIELDS,
  type ProductCreate,
} from "@/features/scan/lib/draftSchema";
import { type DraftCase, scanDraft } from "../../support/drafts";

const c = messages.confirm;
const SCAN_ID = "0b6c1f8e-3c1a-4f0e-9a51-1d2e3f4a5b6c";

afterEach(cleanup);

function setup(name: DraftCase | null, barcode: string | null = null) {
  const onSave = vi.fn<(v: ProductCreate) => void>();
  const draft = name ? scanDraft(name).draft : null;
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      <DraftForm
        draft={draft}
        scanId={name ? SCAN_ID : null}
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

async function saved(onSave: ReturnType<typeof setup>["onSave"]) {
  await user().click(save());
  expect(onSave).toHaveBeenCalledTimes(1);
  return onSave.mock.calls[0]?.[0] as ProductCreate;
}

describe("DraftForm: prefill and blanks", () => {
  it("shows the draft as printed and sends it unchanged with the scan id and barcode", async () => {
    const { onSave, draft } = setup("clean", "8901063201089");
    expect(input("sugars_g").value).toBe("4.2");
    expect(input("added_sugars_g").value).toBe("");
    expect(screen.getByText(c.not_medical_advice)).toBeTruthy();
    const body = await saved(onSave);
    expect(body.scan_id).toBe(SCAN_ID);
    expect(body.barcode).toBe("8901063201089");
    expect(body.basis).toBe("per_100g");
    expect(body.category).toBe("general");
    expect(body.sodium_unit).toBeNull();
    for (const f of ENGINE_FIELDS)
      expect(body.nutrients[f]).toBe(draft?.per_100g[f]);
    expect(body.confirmed_fields).toEqual([]);
  });

  it("draft blanks stay blank, and a cleared field is sent as null, never 0", async () => {
    const { onSave } = setup("clean");
    expect(input("added_sugars_g").value).toBe("");
    await user().clear(input("fiber_g"));
    const body = await saved(onSave);
    expect(body.nutrients.fiber_g).toBeNull();
    expect(body.nutrients.added_sugars_g).toBeNull();
  });

  it("Enter manually: an empty form, nothing preselected, no scan id", async () => {
    const { onSave } = setup(null, "8901063201089");
    for (const f of ["energy_kcal", "sugars_g", "sodium_mg"])
      expect(input(f).value).toBe("");
    expect((screen.getByLabelText(c.name) as HTMLInputElement).value).toBe("");
    for (const r of screen.queryAllByRole("radio") as HTMLInputElement[]) {
      if (r.name !== "veg_mark") expect(r.checked).toBe(false);
    }
    expect(save()).toHaveProperty("disabled", true);
    await user().type(screen.getByLabelText(c.name), "Home Chivda");
    await user().click(
      screen.getByRole("radio", { name: c.category_option.general }),
    );
    await user().click(
      screen.getByRole("radio", { name: c.basis_option.per_100g }),
    );
    await user().type(input("sugars_g"), "12.5");
    const body = await saved(onSave);
    expect("scan_id" in body).toBe(false);
    expect(body.barcode).toBe("8901063201089");
    expect(body.nutrients.sugars_g).toBe(12.5);
    expect(body.nutrients.energy_kcal).toBeNull();
    expect(body.confirmed_fields).toEqual([]);
  });
});

describe("DraftForm: withheld values (R13/R14)", () => {
  it("a withheld protein that isn't ticked is sent without confirming it", async () => {
    const { onSave } = setup("upper_bound_protein");
    expect(within(row("protein_g")).getByText(c.withheld_hint)).toBeTruthy();
    expect(confirmBox("protein_g")).toHaveProperty("checked", false);
    const body = await saved(onSave);
    expect(body.nutrients.protein_g).toBe(0.1);
    expect(body.confirmed_fields).not.toContain("protein_g");
  });

  it("ticking the box confirms it", async () => {
    const { onSave } = setup("upper_bound_protein");
    await user().click(confirmBox("protein_g"));
    expect((await saved(onSave)).confirmed_fields).toContain("protein_g");
  });

  it("editing the value confirms it", async () => {
    const { onSave } = setup("upper_bound_protein");
    await user().clear(input("protein_g"));
    await user().type(input("protein_g"), "0.5");
    const body = await saved(onSave);
    expect(body.confirmed_fields).toContain("protein_g");
    expect(body.nutrients.protein_g).toBe(0.5);
  });
});

describe("DraftForm: warnings", () => {
  it("a code:path warning renders warning.<code>, the field label, and highlights the field", () => {
    setup("upper_bound_protein");
    const banner = screen.getByTestId("warning-upper_bound:per_100g.protein_g");
    expect(within(banner).getByText(messages.warning.upper_bound)).toBeTruthy();
    expect(within(banner).getByText(c.field.protein_g)).toBeTruthy();
    expect(row("protein_g").getAttribute("data-highlight")).toBe("true");
    expect(row("sugars_g").getAttribute("data-highlight")).toBe("false");
  });

  it("highlights implausible field and shows warning", () => {
    setup("implausible_value");
    const banner = screen.getByTestId("warning-implausible_value:sugars_g");
    expect(
      within(banner).getByText(messages.warning.implausible_value),
    ).toBeTruthy();
    expect(within(banner).getByText(c.field.sugars_g)).toBeTruthy();
    expect(row("sugars_g").getAttribute("data-highlight")).toBe("true");
    expect(input("sugars_g").value).toBe("140");
  });

  it("low_confidence is prominent (an alert) and never green", () => {
    setup("low_confidence");
    const banner = screen.getByTestId("warning-low_confidence");
    expect(banner.getAttribute("role")).toBe("alert");
    expect(banner.className).not.toMatch(/verdict-ok/);
    expect(
      within(banner).getByText(messages.warning.low_confidence),
    ).toBeTruthy();
  });
});

describe("DraftForm: forced choices (R17)", () => {
  it("basis_mismatch: save stays disabled until a basis is chosen; printed numbers go out unchanged", async () => {
    const { onSave, draft } = setup("basis_mismatch");
    for (const b of ["per_100g", "per_serving"] as const)
      expect(
        screen.getByRole("radio", { name: c.basis_option[b] }),
      ).toHaveProperty("checked", false);
    expect(save()).toHaveProperty("disabled", true);
    expect(
      within(screen.getByTestId("choice-basis")).getByText(c.choose_required),
    ).toBeTruthy();
    await user().click(
      screen.getByRole("radio", { name: c.basis_option.per_serving }),
    );
    expect(save()).toHaveProperty("disabled", true); // needs a serving size
    await user().type(within(row("serving_size_g")).getByRole("textbox"), "25");
    const body = await saved(onSave);
    expect(body.basis).toBe("per_serving");
    for (const f of ENGINE_FIELDS)
      expect(body.nutrients[f]).toBe(draft?.per_100g[f]);
  });

  it("basis_mismatch: edits made before choosing the basis are kept", async () => {
    const { onSave } = setup("basis_mismatch");
    await user().clear(input("sugars_g"));
    await user().type(input("sugars_g"), "5.5");
    await user().click(
      screen.getByRole("radio", { name: c.basis_option.per_serving }),
    );
    expect(input("sugars_g").value).toBe("5.5");
    await user().type(within(row("serving_size_g")).getByRole("textbox"), "25");
    const body = await saved(onSave);
    expect(body.nutrients.sugars_g).toBe(5.5);
    expect(body.confirmed_fields).toContain("sugars_g");
  });

  it("unit_unconfirmed sodium: save stays disabled until mg or g is chosen; 0.4 stays 0.4", async () => {
    const { onSave } = setup("unit_unconfirmed_sodium");
    expect(save()).toHaveProperty("disabled", true);
    // R19: confirming the sodium value never stands in for the unit.
    await user().click(confirmBox("sodium_mg"));
    expect(save()).toHaveProperty("disabled", true);
    await user().click(screen.getByRole("radio", { name: "g" }));
    const body = await saved(onSave);
    expect(body.sodium_unit).toBe("g");
    expect(body.nutrients.sodium_mg).toBe(0.4);
  });

  it("R19: a sodium unit warning on the other column still needs the picker; the unit shows beside sodium", async () => {
    const { onSave } = setup("unit_unconfirmed_serving_column");
    // Basis per_100g (sodium 740 here), warning is on per_serving.
    expect(
      screen.getByRole("radio", { name: c.basis_option.per_100g }),
    ).toHaveProperty("checked", true);
    expect(screen.getByTestId("choice-sodium_unit")).toBeTruthy();
    expect(save()).toHaveProperty("disabled", true);
    await user().click(screen.getByRole("radio", { name: "mg" }));
    expect(
      within(row("sodium_mg")).getByTestId("sodium-unit").textContent,
    ).toBe(c.sodium_unit_option.mg);
    const body = await saved(onSave);
    expect(body.sodium_unit).toBe("mg");
    expect(body.nutrients.sodium_mg).toBe(740);
  });

  it("no sodium unit warning: sodium stays labelled in mg and no picker", () => {
    setup("clean");
    expect(screen.queryByTestId("choice-sodium_unit")).toBeNull();
    expect(
      within(row("sodium_mg")).getByTestId("sodium-unit").textContent,
    ).toBe(c.sodium_unit_option.mg);
  });

  it("category_check keeps save disabled until a category is chosen; the body carries it", async () => {
    const { onSave } = setup("category_check");
    for (const r of screen.getAllByRole("radio", {
      name: (n) => (Object.values(c.category_option) as string[]).includes(n),
    }))
      expect(r).toHaveProperty("checked", false);
    expect(save()).toHaveProperty("disabled", true);
    expect(
      within(screen.getByTestId("choice-category")).getByText(
        c.choose_required,
      ),
    ).toBeTruthy();
    await user().click(
      screen.getByRole("radio", { name: c.category_option.beverage }),
    );
    expect((await saved(onSave)).category).toBe("beverage");
  });
});

describe("DraftForm: serving size (R18/R19)", () => {
  it("serving_size_g is confirmed only after a tick", async () => {
    const { onSave } = setup("clean");
    expect(input("serving_size_g").value).toBe("40");
    expect(confirmBox("serving_size_g")).toHaveProperty("checked", false);
    let body = await saved(onSave);
    expect(body.serving_size_g).toBe(40);
    expect(body.confirmed_fields).not.toContain("serving_size_g");
    await user().click(confirmBox("serving_size_g"));
    await user().click(save());
    body = onSave.mock.calls[1]?.[0] as ProductCreate;
    expect(body.confirmed_fields).toContain("serving_size_g");
  });

  it("serving_size_g is confirmed after an edit", async () => {
    const { onSave } = setup("clean");
    await user().clear(input("serving_size_g"));
    await user().type(input("serving_size_g"), "30");
    const body = await saved(onSave);
    expect(body.serving_size_g).toBe(30);
    expect(body.confirmed_fields).toContain("serving_size_g");
  });

  it("derived_from_serving: shows the printed per-serving column and the serving size, basis per_serving", async () => {
    const { onSave, draft } = setup("derived_from_serving");
    expect(
      screen.getByRole("radio", { name: c.basis_option.per_serving }),
    ).toHaveProperty("checked", true);
    expect(input("sugars_g").value).toBe("6"); // printed, not the derived 20
    expect(input("serving_size_g").value).toBe("30");
    expect(
      screen.getByText(c.derived_per_serving.replace("{serving}", "30")),
    ).toBeTruthy();
    // R19: the serving size must be ticked before saving.
    expect(save()).toHaveProperty("disabled", true);
    await user().click(confirmBox("serving_size_g"));
    const body = await saved(onSave);
    expect(body.basis).toBe("per_serving");
    expect(body.serving_size_g).toBe(30);
    expect(body.confirmed_fields).toContain("serving_size_g");
    for (const f of ENGINE_FIELDS)
      expect(body.nutrients[f]).toBe(draft?.per_serving?.[f]);
  });

  it("R19: derived + basis_mismatch still needs the serving-size tick", async () => {
    const { onSave } = setup("derived_basis_mismatch");
    expect(save()).toHaveProperty("disabled", true);
    await user().click(
      screen.getByRole("radio", { name: c.basis_option.per_serving }),
    );
    expect(save()).toHaveProperty("disabled", true);
    await user().click(confirmBox("serving_size_g"));
    expect(save()).toHaveProperty("disabled", false);
    expect((await saved(onSave)).confirmed_fields).toContain("serving_size_g");
  });

  it("R19: never shows or sends the server-derived per_100g as printed", async () => {
    const { onSave } = setup("derived_from_serving");
    await user().click(
      screen.getByRole("radio", { name: c.basis_option.per_100g }),
    );
    expect(input("sugars_g").value).toBe(""); // not 20
    expect(input("energy_kcal").value).toBe(""); // not 500
    await user().click(confirmBox("serving_size_g"));
    const body = await saved(onSave);
    expect(body.basis).toBe("per_100g");
    for (const f of ENGINE_FIELDS) expect(body.nutrients[f]).toBeNull();
  });
});

describe("DraftForm: allergens and ingredients", () => {
  it("Devanagari ingredients round-trip unchanged into the body", async () => {
    const { onSave, draft } = setup("devanagari");
    expect(screen.getByDisplayValue("बेसन (चने का आटा)")).toBeTruthy();
    expect(screen.getByDisplayValue("इसमें मूँगफली है।")).toBeTruthy();
    const body = await saved(onSave);
    expect(body.ingredients).toEqual(draft?.ingredients);
    expect(body.allergen_statement).toBe(draft?.allergen_statement);
    expect(body.may_contain_statement).toBe(draft?.may_contain_statement);
    expect(body.name).toBe("नमकीन मिक्स");
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
      "Spices and condiments",
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
    expect(body.may_contain_statement).toBe("May contain milk and soy.");
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
