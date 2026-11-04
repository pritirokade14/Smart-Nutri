import { expect, test } from "@playwright/test";
import { SESSION_COOKIE, STUB, signIn } from "./support/session";

// Profile → Delete account (Plan 8 Task 2) against the stub API: the first
// DELETE /v1/me answers 503 deletion_incomplete and the client retries.

test("delete account: typed confirmation, retry on 503, signed out, goodbye", async ({
  page,
  context,
  request,
}) => {
  await request.post(`${STUB}/__reset?terms=current&delete_fails=1`);
  await signIn(context);
  const violations: string[] = [];
  page.on("console", (m) => {
    if (/content security policy/i.test(m.text())) violations.push(m.text());
  });

  await page.goto("/en/profile");
  await expect(
    page.getByRole("heading", { level: 2, name: "Language" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Delete account" }).click();
  const dialog = page.getByTestId("delete-dialog");
  const confirm = dialog.getByRole("button", { name: "Delete permanently" });
  await expect(confirm).toBeDisabled();
  await dialog.getByLabel("Type DELETE to confirm").fill("DELETE");
  await confirm.click();

  await expect(page).toHaveURL(/\/en\/goodbye$/, { timeout: 15_000 });
  await expect(
    page.getByRole("heading", { name: "Your account has been deleted" }),
  ).toBeVisible();
  const state = (await (await request.get(`${STUB}/__state`)).json()) as {
    deleted: boolean;
    deleteFails: number;
  };
  expect(state).toMatchObject({ deleted: true, deleteFails: 0 });
  expect(
    (await context.cookies()).filter((c) => c.name.startsWith(SESSION_COOKIE)),
  ).toEqual([]);

  // The session is gone: logged-in pages go back to sign-in.
  await page.goto("/en/home");
  await expect(page).toHaveURL(/\/en\/sign-in/);
  expect(violations).toEqual([]);
});

test("the profile (and Delete account) stays reachable before agreeing to terms", async ({
  page,
  context,
  request,
}) => {
  await request.post(`${STUB}/__reset`);
  await signIn(context);
  await page.goto("/en/profile");
  await expect(page.getByTestId("terms-step")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Delete account" }),
  ).toBeVisible();
});
