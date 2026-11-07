import {
  type APIRequestContext,
  type BrowserContext,
  expect,
  test,
} from "@playwright/test";
import { STUB, signIn } from "./support/session";

// The daily guide (Plan 10, slice 1) against the stub API (e2e/stub-api.mjs):
// the stub serves the golden targets chosen from what was posted and never
// computes a number. The web app renders what it is sent.

const AUTH = { authorization: "Bearer e2e" };

async function start(
  context: BrowserContext,
  request: APIRequestContext,
  query = "terms=current&health_data=current&user_types=weight_loss",
) {
  await request.post(`${STUB}/__reset?${query}`);
  await signIn(context);
}

const saveGuide = (
  request: APIRequestContext,
  body: Record<string, unknown> = {},
) =>
  request.put(`${STUB}/v1/targets/settings`, {
    headers: AUTH,
    data: {
      direction: "lose",
      activity_level: "light",
      pregnant_or_breastfeeding: false,
      numbers_display: "show",
      ...body,
    },
  });

test("set up lose weight and see the guide", async ({
  page,
  context,
  request,
}) => {
  await start(context, request);
  await page.goto("/en/home");

  // Weight Loss mode: the daily guide card comes first, with the setup CTA.
  const card = page.getByTestId("home-card-today_targets");
  await expect(card).toBeVisible();
  await card.getByRole("link", { name: "Set up your daily guide" }).click();
  await expect(page).toHaveURL(/\/en\/guide\/setup$/);

  // Intro: "show numbers" is preselected.
  await expect(page.getByRole("radio", { name: "Show numbers" })).toBeChecked();
  await page.getByRole("button", { name: "Continue" }).click();

  // About you.
  await page.getByLabel("Year of birth").fill("1990");
  await page.getByLabel("Sex (optional)").selectOption("female");
  await page.getByLabel("Height (cm, optional)").fill("165");
  await page.getByLabel("Weight (kg, optional)").fill("80");
  await page.getByRole("button", { name: "Continue" }).click();

  // Activity, then the goal.
  await page.getByRole("radio", { name: /Lightly active/ }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("radio", { name: "Lose weight slowly" }).check();
  await page.getByRole("button", { name: "Continue" }).click();

  // The guide, exactly as the API sent it.
  const rows = page.getByTestId("guide-rows");
  await expect(rows).toContainText("1,540 kcal");
  await expect(rows).toContainText("71 g");
  await expect(
    page.getByText(
      "Information, not medical advice. Daily guides are estimates and are pending clinician review.",
    ),
  ).toBeVisible();
  await page.getByRole("button", { name: "Save my daily guide" }).click();

  await expect(page).toHaveURL(/\/en\/home$/);
  await expect(page.getByTestId("home-card-today_targets")).toContainText(
    "1,540 kcal",
  );
});

test("hide all numbers leaves no digits on the Today card", async ({
  page,
  context,
  request,
}) => {
  await start(context, request);
  await saveGuide(request);
  await page.goto("/en/home");

  const card = page.getByTestId("home-card-today_targets");
  await expect(card).toContainText("1,540 kcal");
  await card.getByRole("button", { name: "Hide numbers" }).click();
  await expect(
    card.getByRole("button", { name: "Show numbers" }),
  ).toBeVisible();
  await expect(card).toContainText(
    "Numbers are hidden. You can change this in settings.",
  );
  // Title, note and disclaimer only: not one digit.
  await expect(card).not.toHaveText(/\d/);
  // One tap brings them back.
  await card.getByRole("button", { name: "Show numbers" }).click();
  await expect(card).toContainText("1,540 kcal");
});

test("without health_data the guide shows the consent card and Home still works", async ({
  page,
  context,
  request,
}) => {
  await start(context, request, "terms=current&user_types=weight_loss");
  await page.goto("/en/home");

  const card = page.getByTestId("home-card-today_targets");
  await expect(
    card.getByText(
      "To see your daily guide, allow SmartNutri to use your health details.",
    ),
  ).toBeVisible();
  // Not a redirect and no consent screen pulled over Home.
  await expect(page).toHaveURL(/\/en\/home$/);
  await expect(page.getByTestId("consent-dialog")).toHaveCount(0);
  await expect(page.getByTestId("home-card-recent_scans")).toBeVisible();
  await expect(
    page.getByRole("link", { name: /Scan a barcode/i }),
  ).toBeVisible();

  // The grant button opens the health-data consent; agreeing loads the guide.
  await card.getByRole("button", { name: "I agree" }).click();
  await page
    .getByTestId("consent-dialog")
    .getByRole("button", { name: "I agree" })
    .click();
  await expect(card.getByText("Set up your daily guide")).toBeVisible();
});

test("body fat 15 moves protein to lean mass and clearing it moves it back", async ({
  page,
  context,
  request,
}) => {
  await start(context, request);
  await saveGuide(request, { direction: "maintain" });
  await page.goto("/en/profile/guide");

  const protein = page.locator('[data-line="protein"]');
  await expect(protein).toHaveText(
    "Protein: 1.6 g per kg of your weight (70 kg)",
  );

  const fat = page.getByLabel("Body fat % (optional)");
  await fat.fill("15");
  await expect(protein).toHaveText(
    "Protein: 2 g per kg of lean mass (59.5 kg)",
  );

  await fat.fill("");
  await expect(protein).toHaveText(
    "Protein: 1.6 g per kg of your weight (70 kg)",
  );
});
