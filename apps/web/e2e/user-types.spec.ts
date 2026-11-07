import { expect, type Page, test } from "@playwright/test";
import { STUB, signIn } from "./support/session";

// "What brings you to SmartNutri?" (Plan 9, T12/T13) against the stub API:
// terms first, then the picker, follow-ups, the in-place health consent,
// and the confirm-only pre-fill review. Nothing reaches the member until
// "Add to profile".

const stubState = async (page: Page) =>
  (await (await page.request.get(`${STUB}/__state`)).json()) as {
    userTypes: { types: string[]; follow_ups: Record<string, unknown> } | null;
    members: { allergens: string[]; goal: string | null }[];
    consents: Record<string, string | null>;
  };

test("first sign-in: terms, then the picker, follow-ups and a confirmed pre-fill", async ({
  page,
  context,
  request,
}) => {
  await request.post(`${STUB}/__reset?user_types=unanswered`);
  await signIn(context);

  await page.goto("/en/home");
  await page
    .getByTestId("terms-step")
    .getByRole("button", { name: "I agree" })
    .click();

  // Unanswered: the app goes to the picker.
  await expect(page).toHaveURL(/\/en\/welcome$/);
  await expect(
    page.getByRole("heading", { name: "What brings you to SmartNutri?" }),
  ).toBeVisible();
  await page.getByTestId("type-tile-gym").click();
  await page.getByTestId("type-tile-allergy_diet").click();
  await page.getByRole("button", { name: "Continue" }).click();

  // One follow-up per type, allergy first (priority).
  await page.getByRole("radio", { name: "Build muscle" }).check();
  await page.getByRole("button", { name: "Milk", exact: true }).click();
  await page.getByRole("button", { name: "Continue" }).click();

  // Allergy is health data: the existing consent dialog opens in place.
  const dialog = page.getByTestId("consent-dialog");
  await dialog.getByRole("button", { name: "I agree" }).click();

  // Review: both come from the user's own answers, so both start ticked.
  const review = page.getByTestId("prefill-review");
  await expect(
    review.getByRole("heading", { name: "Add these to your profile?" }),
  ).toBeVisible();
  const allergy = review.getByRole("checkbox", { name: "Allergies: Milk" });
  const goal = review.getByRole("checkbox", { name: "Goal: Build muscle" });
  await expect(allergy).toBeChecked();
  await expect(goal).toBeChecked();
  // Saved types, but the member is untouched until confirmed.
  let s = await stubState(page);
  expect(s.userTypes?.types).toEqual(["gym", "allergy_diet"]);
  expect(s.members[0]?.allergens).toEqual([]);
  expect(s.members[0]?.goal).toBeNull();

  await review.getByRole("button", { name: "Add to profile" }).click();
  // Gym is a daily-guide mode (Plan 10): the guide setup is offered, skippable.
  await expect(page).toHaveURL(/\/en\/guide\/setup\?from=welcome$/);
  await page.getByRole("button", { name: "Skip, just log food" }).click();
  await expect(page).toHaveURL(/\/en\/home$/);
  s = await stubState(page);
  expect(s.members[0]?.allergens).toEqual(["milk"]);
  expect(s.members[0]?.goal).toBe("build_muscle");
  expect(s.consents.health_data).toBe("2026-11-01");

  // Home is in the allergy_diet mode (priority over gym): its tabs, and the
  // allergy card first.
  const nav = page.getByRole("navigation", { name: "Main navigation" });
  await expect(nav.getByTestId("nav-tab")).toHaveText([
    "Home",
    "Scan",
    "Family",
    "Search",
    "Profile",
  ]);
  await expect(page.getByTestId(/^home-card-/).first()).toHaveAttribute(
    "data-testid",
    "home-card-allergy_check",
  );
  await expect(
    page.getByTestId("home-card-allergy_check").getByText("You: Milk"),
  ).toBeVisible();
  // The switcher shows both types; switching changes the tabs at once.
  const switcher = page.getByRole("radiogroup", { name: "Mode" });
  await expect(switcher.getByRole("radio")).toHaveText([
    "Allergy or diet",
    "Gym and fitness",
  ]);
  await switcher.getByRole("radio", { name: "Gym and fitness" }).click();
  await expect(nav.getByTestId("nav-tab")).toHaveText([
    "Home",
    "Scan",
    "Protein",
    "Compare",
    "Profile",
  ]);
  // Nothing is lost: the rest is under More.
  await page.getByRole("button", { name: "More" }).click();
  await expect(page.getByTestId("more-dialog").getByRole("link")).toHaveText([
    "History",
    "Family",
    "Search",
    "How we score",
  ]);
  await page.keyboard.press("Escape");
  await nav.getByRole("link", { name: "Protein" }).click();
  await expect(page).toHaveURL(/\/en\/protein$/);
  await expect(
    page.getByRole("heading", { level: 1, name: "Protein" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Higher-protein options" }),
  ).toBeVisible();

  // Answered: /welcome without ?edit=1 goes home.
  await page.goto("/en/welcome");
  await expect(page).toHaveURL(/\/en\/home$/);
});

test("skip for now stores no types and lands on Home", async ({
  page,
  context,
  request,
}) => {
  await request.post(`${STUB}/__reset?terms=current&user_types=unanswered`);
  await signIn(context);
  await page.goto("/en/history");
  await expect(page).toHaveURL(/\/en\/welcome$/);
  await page.getByRole("button", { name: "Skip for now" }).click();
  await expect(page).toHaveURL(/\/en\/home$/);
  expect((await stubState(page)).userTypes?.types).toEqual([]);
});
