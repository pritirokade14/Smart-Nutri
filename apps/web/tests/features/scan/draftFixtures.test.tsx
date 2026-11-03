import messages from "@smartnutri/i18n/messages/en.json";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DraftForm } from "@/features/scan/components/DraftForm";
import { BASES, type ProductCreate } from "@/features/scan/lib/draftSchema";
import {
  draftCaseFiles,
  draftFile,
  expectedDrafts,
  SCAN_ID,
  type ScriptedSave,
} from "../../support/drafts";

/**
 * Shared fixture test (AGENTS.md rule 11, Rulings R21/R23): every scripted
 * save in packages/test-fixtures/drafts/expected.json is driven through the
 * real form, and the body the form would POST must equal the expected body
 * exactly (an edit confirms, as the fixtures now record).
 *
 * A save marked `client_blocks: true` (serving_required without a confirmed
 * serving) or one that needs a missing choice (`body.basis`, `body.category`,
 * `body.sodium_unit`) keeps save disabled and sends nothing. Every other
 * scripted save, including 422 `implausible_value`, is sent exactly as expected.
 */

const c = messages.confirm;
const expected = expectedDrafts();
const CHOICE_FIELDS = new Set([
  "body.basis",
  "body.category",
  "body.sodium_unit",
]);

afterEach(cleanup);

function blockedBy(save: ScriptedSave): string | null {
  if (
    save.result.status === 422 &&
    save.result.error.fields.some((f) => CHOICE_FIELDS.has(f))
  )
    return "missing choice";
  if (save.client_blocks === true) return "serving not confirmed";
  return null;
}

const row = (field: string) => screen.getByTestId(`row-${field}`);
const saveButton = () => screen.getByRole("button", { name: c.save });
const boxFields = () =>
  screen
    .queryAllByTestId(/^confirm-/)
    .map((el) => el.getAttribute("data-testid")?.slice("confirm-".length))
    .sort();

describe("shared confirm-screen fixtures (packages/test-fixtures/drafts)", () => {
  it("expected.json covers every draft file and nothing else", () => {
    expect(expected.format_version).toBe(1);
    const referenced = Object.values(expected.cases)
      .map((k) => k.draft)
      .sort();
    expect(referenced).toEqual(draftCaseFiles());
    expect(Object.keys(expected.cases).length).toBeGreaterThan(0);
  });

  for (const [name, kase] of Object.entries(expected.cases)) {
    describe(name, () => {
      it("initial render follows draft.confirm only", () => {
        const draft = draftFile(kase.draft);
        render(
          <NextIntlClientProvider locale="en" messages={messages}>
            <DraftForm draft={draft} scanId={SCAN_ID} onSave={vi.fn()} />
          </NextIntlClientProvider>,
        );
        const hints = draft.confirm;
        const offered = BASES.filter((b) => hints.columns[b] !== null);
        // R22: in doubt, nothing; else the only column, or per_100g of two.
        const preselect = hints.basis_required
          ? null
          : offered.length > 1
            ? "per_100g"
            : (offered[0] ?? null);
        for (const b of BASES) {
          const radio = within(screen.getByTestId("choice-basis")).getByRole(
            "radio",
            { name: c.basis_option[b] },
          ) as HTMLInputElement;
          expect(radio.checked).toBe(b === preselect);
          expect(radio.disabled).toBe(!offered.includes(b));
        }
        const categoryChecked = within(
          screen.getByTestId("choice-category"),
        ).queryAllByRole("radio", { checked: true }) as HTMLInputElement[];
        expect(categoryChecked.map((r) => r.value)).toEqual(
          hints.category_required ? [] : [draft.category],
        );
        // Never pre-ticked.
        for (const box of screen.queryAllByTestId(/^confirm-/))
          expect((box as HTMLInputElement).checked).toBe(false);
        // A preselected basis shows exactly its column's boxes.
        if (preselect) {
          expect(boxFields()).toEqual(
            [...(hints.columns[preselect]?.confirm_fields ?? [])].sort(),
          );
        }
      });

      kase.saves.forEach((save, i) => {
        it(`save ${i}: ${JSON.stringify(save.actions)} → ${save.result.status}`, async () => {
          const draft = draftFile(kase.draft);
          const onSave = vi.fn<(v: ProductCreate) => void>();
          render(
            <NextIntlClientProvider locale="en" messages={messages}>
              <DraftForm draft={draft} scanId={SCAN_ID} onSave={onSave} />
            </NextIntlClientProvider>,
          );
          const user = userEvent.setup();
          const a = save.actions;

          if (a.pick_basis)
            await user.click(
              within(screen.getByTestId("choice-basis")).getByRole("radio", {
                name: c.basis_option[a.pick_basis],
              }),
            );
          if (a.pick_category)
            await user.click(
              within(screen.getByTestId("choice-category")).getByRole("radio", {
                name: c.category_option[a.pick_category],
              }),
            );
          for (const [field, value] of Object.entries(a.edit ?? {})) {
            const input = within(row(field)).getByRole("textbox");
            await user.clear(input);
            if (value !== null) await user.type(input, String(value));
          }
          if (a.sodium_unit)
            await user.click(
              within(screen.getByTestId("choice-sodium_unit")).getByRole(
                "radio",
                { name: c.sodium_unit_option[a.sodium_unit] },
              ),
            );

          // Once a basis is in effect, the boxes are exactly that column's
          // confirm_fields: never all nine on a basis_mismatch draft.
          const basis = save.body.basis as keyof typeof draft.confirm.columns;
          if (basis) {
            const cols = draft.confirm.columns;
            expect(boxFields()).toEqual(
              [...(cols[basis]?.confirm_fields ?? [])].sort(),
            );
            // A shared printed column says which basis it is saved as.
            const shownCol = cols[basis]?.printed
              ? cols[basis]
              : BASES.map((b) => cols[b]).find((col) => col?.shared);
            const label = screen.queryByTestId("shared-basis");
            if (shownCol?.shared)
              expect(label?.textContent).toBe(c.basis_option[basis]);
            else expect(label).toBeNull();
          }

          for (const f of a.tick ?? []) {
            const box = screen.getByTestId(`confirm-${f}`) as HTMLInputElement;
            expect(box.checked).toBe(false);
            await user.click(box);
          }

          const reason = blockedBy(save);
          if (reason) {
            expect(saveButton()).toHaveProperty("disabled", true);
            await user.click(saveButton());
            expect(onSave).not.toHaveBeenCalled();
            return;
          }
          expect(saveButton()).toHaveProperty("disabled", false);
          await user.click(saveButton());
          expect(onSave).toHaveBeenCalledTimes(1);
          const { scan_id, ...body } = onSave.mock.calls[0]?.[0] ?? {};
          expect(scan_id).toBe(SCAN_ID);
          expect(body).toStrictEqual(save.body);
        });
      });
    });
  }
});
