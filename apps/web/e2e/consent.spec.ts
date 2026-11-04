import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, type Page, test } from "@playwright/test";
import { STUB, signIn } from "./support/session";

// Terms acceptance (F11, ADR 0018, ruling G1) against the stub API, which
// gates POST /v1/analyze on `terms` like the real one.

const FIXTURES = join(process.cwd(), "../../packages/test-fixtures");
const SF_BISCUIT = (
  JSON.parse(readFileSync(join(FIXTURES, "responses/index.json"), "utf8")) as {
    products: Record<string, string>;
  }
).products.sf_biscuit as string;

const stubState = async (page: Page) =>
  (await (await page.request.get(`${STUB}/__state`)).json()) as {
    consents: Record<string, string | null>;
  };

function cspWatch(page: Page): string[] {
  const violations: string[] = [];
  page.on("console", (m) => {
    if (/content security policy/i.test(m.text())) violations.push(m.text());
  });
  return violations;
}

test("first sign-in asks for terms before anything else, then opens the app", async ({
  page,
  context,
  request,
}) => {
  await request.post(`${STUB}/__reset`);
  await signIn(context);
  const violations = cspWatch(page);

  await page.goto("/en/home");
  const step = page.getByTestId("terms-step");
  await expect(
    step.getByRole("heading", { name: "Before you start" }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: /^Hello/ })).toHaveCount(0);
  await expect(
    step.getByRole("link", { name: "Terms of use" }),
  ).toHaveAttribute("href", "/en/terms");
  await expect(
    step.getByRole("link", { name: "Privacy notice" }),
  ).toHaveAttribute("href", "/en/privacy");
  await expect(
    step.getByText("Information, not medical advice."),
  ).toBeVisible();

  await step.getByRole("button", { name: "I agree" }).click();
  await expect(page.getByRole("heading", { name: /^Hello/ })).toBeVisible();
  expect((await stubState(page)).consents.terms).toBe("2026-11-01");
  // AI explanations stay optional and unticked.
  expect((await stubState(page)).consents.ai_processing).toBeNull();

  // Agreed once: the next page opens directly.
  await page.goto(`/en/product/${SF_BISCUIT}`);
  await expect(page.getByTestId("verdict-card").first()).toBeVisible();
  expect(violations).toEqual([]);
});

test("updated terms (needs_update) are asked for again", async ({
  page,
  context,
  request,
}) => {
  await request.post(`${STUB}/__reset?terms=old`);
  await signIn(context);
  await page.goto("/en/home");
  await expect(
    page.getByRole("heading", { name: "We've updated our terms" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "I agree" }).click();
  await expect(page.getByRole("heading", { name: /^Hello/ })).toBeVisible();
  expect((await stubState(page)).consents.terms).toBe("2026-11-01");
});

test("withdrawing terms on the profile stops checking products until agreed again", async ({
  page,
  context,
  request,
}) => {
  await request.post(`${STUB}/__reset?terms=current`);
  await signIn(context);
  await page.goto("/en/profile");
  const terms = page.getByTestId("consent-terms");
  await terms.getByRole("button", { name: "Withdraw consent" }).click();
  await page
    .getByTestId("confirm-dialog")
    .getByRole("button", { name: "Withdraw consent" })
    .click();
  await expect(terms.getByTestId("consent-state")).toHaveText("Not agreed");
  expect((await stubState(page)).consents.terms).toBeNull();

  await page.goto(`/en/product/${SF_BISCUIT}`);
  await expect(page.getByTestId("terms-step")).toBeVisible();
  await expect(page.getByTestId("verdict-card")).toHaveCount(0);
});

test("a consent_required answer from a gated route shows the terms step", async ({
  page,
  context,
  request,
}) => {
  await request.post(`${STUB}/__reset?terms=current`);
  await signIn(context);
  // Terms read as agreed when the page loads, then the server refuses the
  // analyze call (withdrawn on another device): the gate takes over.
  await page.route(
    "**/v1/consents",
    async (route) => {
      const res = await route.fetch();
      await request.post(`${STUB}/__reset`);
      await route.fulfill({ response: res });
    },
    { times: 1 },
  );
  await page.goto(`/en/product/${SF_BISCUIT}`);
  await expect(page.getByTestId("terms-step")).toBeVisible();
  await expect(page.getByTestId("verdict-card")).toHaveCount(0);
});
