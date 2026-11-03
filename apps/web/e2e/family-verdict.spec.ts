import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import { STUB, signIn } from "./support/session";

// Signed-in family flow against the stub API (Ruling P5-R23): add "Dad"
// (diabetes, after health-data consent), then open the sugar-free biscuit:
// Dad's card shows the avoid colour and the misleading-claim line. The stub
// (e2e/stub-api.mjs) also stands in for Supabase Auth, so a session cookie
// with an HS256 token is accepted by getClaims() through GET /auth/v1/user.
// The verdict itself is the golden sf_biscuit/diabetic_adult response.

const FIXTURES = join(process.cwd(), "../../packages/test-fixtures");
const SF_BISCUIT = (
  JSON.parse(readFileSync(join(FIXTURES, "responses/index.json"), "utf8")) as {
    products: Record<string, string>;
  }
).products.sf_biscuit as string;
const misleadingClaim = (
  JSON.parse(readFileSync(join(FIXTURES, "reason-text/en.json"), "utf8")) as {
    product: string;
    member: string;
    reason: { code: string };
    text: string;
  }[]
).find(
  (e) =>
    e.product === "sf_biscuit" &&
    e.member === "diabetic_adult" &&
    e.reason.code === "misleading_sugar_claim",
)?.text as string;

test.beforeEach(async ({ context, request }) => {
  // Terms already agreed: the terms step has its own spec (consent.spec.ts).
  await request.post(`${STUB}/__reset?terms=current`);
  await signIn(context);
});

test("add Dad (diabetes, after consent), then his card on the sugar-free biscuit", async ({
  page,
}) => {
  expect(misleadingClaim).toBeTruthy();
  const violations: string[] = [];
  page.on("console", (m) => {
    if (/content security policy/i.test(m.text())) violations.push(m.text());
  });

  await page.goto("/en/family");
  await expect(
    page.getByRole("heading", { level: 1, name: "Family" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Add a family member" }).click();
  await expect(page).toHaveURL(/\/en\/members\/new$/);

  await page.getByLabel("Name").fill("Dad");
  await page.getByLabel("Relation").selectOption("parent");
  await page.getByLabel("Year of birth").fill("1960");
  await page.getByLabel("Diabetes", { exact: true }).check();
  await page.getByRole("button", { name: "Save" }).click();

  // Health data needs consent first; AI explanations stay optional.
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(
    dialog.getByRole("heading", { name: "Health data" }),
  ).toBeVisible();
  await dialog.getByRole("button", { name: "I agree" }).click();

  await expect(page).toHaveURL(/\/en\/family$/);
  await expect(
    page.getByTestId("member-row").filter({ hasText: "Dad" }),
  ).toBeVisible();

  await page.goto(`/en/product/${SF_BISCUIT}`);
  const card = page
    .getByTestId("verdict-card")
    .filter({ has: page.getByRole("heading", { name: "Avoid for Dad" }) });
  await expect(card).toBeVisible();
  await expect(card).toHaveAttribute("data-verdict", "avoid");
  await expect(card.getByText(misleadingClaim)).toBeVisible();

  // The card's accent is the avoid token colour (never computed in the browser).
  const [accent, avoid] = await card.evaluate((el) => {
    const probe = document.createElement("span");
    probe.style.color = "var(--color-verdict-avoid)";
    document.body.append(probe);
    const want = getComputedStyle(probe).color;
    probe.remove();
    return [getComputedStyle(el).borderInlineStartColor, want];
  });
  expect(accent).toBe(avoid);

  // The account holder's card says "for you"; the label claim is checked.
  await expect(
    page.getByRole("heading", { name: "Label unclear for you" }),
  ).toBeVisible();
  await expect(page.getByTestId("claims-section")).toContainText(
    "Label says: Sugar free",
  );
  await expect(page.getByTestId("explanation-card")).toHaveCount(0);
  await expect(page.getByText("Information, not medical advice.")).toHaveCount(
    1,
  );
  expect(violations).toEqual([]);
});
