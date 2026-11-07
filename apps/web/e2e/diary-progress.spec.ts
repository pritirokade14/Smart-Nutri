import { expect, type Page, test } from "@playwright/test";
import { STUB, signIn } from "./support/session";

// The Progress view and the weight log against the stub API
// (e2e/stub-api.mjs). The stub echoes weigh-ins as the trend and never
// decides anything: every number on screen is what the stub returned.

const AUTH = { authorization: "Bearer e2e" };

const istDay = (offset = 0): string => {
  const d = new Date(Date.now() + 330 * 60_000);
  d.setUTCDate(d.getUTCDate() + offset);
  return d.toISOString().slice(0, 10);
};

/** Digits left on the page once dates and day counts are removed. */
async function digits(page: Page): Promise<string> {
  return page.evaluate(() => {
    const root = (document.querySelector("main") as HTMLElement).cloneNode(
      true,
    ) as HTMLElement;
    for (const el of root.querySelectorAll("[data-allow-digits]")) el.remove();
    return (root.textContent ?? "").replace(/\D/g, "");
  });
}

async function addWeighIn(page: Page, date: string, kg: string) {
  await page.getByTestId("weight-add").click();
  const dialog = page.getByTestId("weigh-in-dialog");
  await dialog.getByLabel("Date").fill(date);
  await dialog.getByLabel("Weight", { exact: true }).fill(kg);
  await dialog.getByRole("button", { name: "Save" }).click();
  return dialog;
}

test.describe("with health data agreed", () => {
  test.beforeEach(async ({ context, request }) => {
    await request.post(`${STUB}/__reset?terms=current&health_data=current`);
    await signIn(context);
  });

  test("two weigh-ins show the trend and no projection; a third needs confirming", async ({
    page,
  }) => {
    await page.goto("/en/diary?view=progress");
    await expect(page.getByTestId("weight-empty-chart")).toBeVisible();

    const first = await addWeighIn(page, istDay(-2), "80");
    await expect(first).toBeHidden();
    await addWeighIn(page, istDay(-1), "79.5");
    await expect(page.getByTestId("weight-chart")).toBeVisible();
    await expect(page.getByTestId("weight-trend-line")).toBeVisible();
    await expect(page.getByTestId("weight-row")).toHaveCount(2);
    await expect(page.getByTestId("weight-no-projection")).toHaveText(
      "Add a few more weigh-ins over a couple of weeks to see a projection.",
    );
    await expect(page.getByTestId("weight-projection")).toHaveCount(0);

    // A big jump asks first.
    const dialog = await addWeighIn(page, istDay(0), "65");
    await expect(page.getByTestId("weight-confirm")).toContainText(
      "This is quite different from your last weigh-in (79.5 kg). Save anyway?",
    );
    await page.getByTestId("weight-save-anyway").click();
    await expect(dialog).toBeHidden();
    await expect(page.getByTestId("weight-row")).toHaveCount(3);
  });

  test("an out-of-range weight shows the API's message", async ({ page }) => {
    await page.goto("/en/diary?view=progress");
    await addWeighIn(page, istDay(0), "500");
    await expect(page.getByTestId("weight-error")).toHaveText(
      "Enter a weight between 2 and 300 kg.",
    );
  });

  test("edit and delete a weigh-in", async ({ page, request }) => {
    await request.put(`${STUB}/v1/weights/${istDay(-1)}`, {
      headers: AUTH,
      data: { weight_kg: 80 },
    });
    await page.goto("/en/diary?view=progress");
    const row = page.getByTestId("weight-row");
    await expect(row).toContainText("80 kg");
    await page.getByTestId("weight-edit").click();
    const dialog = page.getByTestId("weigh-in-dialog");
    await dialog.getByLabel("Weight", { exact: true }).fill("79");
    await dialog.getByRole("button", { name: "Save" }).click();
    await expect(dialog).toBeHidden();
    await expect(row).toContainText("79 kg");
    await page.getByTestId("weight-delete").click();
    await page
      .getByTestId("confirm-dialog")
      .getByRole("button", { name: "Delete weigh-in" })
      .click();
    await expect(page.getByTestId("weight-empty")).toBeVisible();
  });

  test("hiding all numbers leaves no digits on Progress", async ({
    page,
    request,
  }) => {
    for (const [i, kg] of [80, 79.5, 79].entries()) {
      await request.put(`${STUB}/v1/weights/${istDay(-3 + i)}`, {
        headers: AUTH,
        data: { weight_kg: kg },
      });
    }
    await request.put(`${STUB}/v1/targets/settings`, {
      headers: AUTH,
      data: {
        activity_level: "light",
        direction: "maintain",
        energy_mode: "formula",
        numbers_display: "show",
        pregnant_or_breastfeeding: false,
      },
    });
    await page.goto("/en/diary");
    await page.getByTestId("eye-toggle").click();
    await page.getByRole("button", { name: "Progress" }).click();
    await expect(page.getByTestId("weight-chart")).toBeVisible();
    await expect(page.getByTestId("weight-row")).toHaveCount(3);
    await expect(page.getByTestId("weight-dot")).toHaveCount(3);
    expect(await digits(page)).toBe("");
  });

  test("withdrawing health data shows the consent card; the diary still loads", async ({
    page,
    request,
  }) => {
    await request.post(`${STUB}/v1/consents`, {
      headers: AUTH,
      data: { purpose: "health_data", granted: false, version: "2026-11-01" },
    });
    await page.goto("/en/diary?view=progress");
    await expect(page.getByTestId("weight-consent")).toContainText(
      "To keep a weight log, allow SmartNutri to use your health details.",
    );
    await expect(page.getByTestId("weight-chart")).toHaveCount(0);
    await page.getByRole("button", { name: "Day" }).click();
    await expect(page.getByTestId("day-title")).toHaveText("Today");
  });
});
