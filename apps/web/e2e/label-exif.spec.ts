import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import { STUB, signIn } from "./support/session";

// The label photo a phone writes carries the location (EXIF GPS). In a real
// browser, the photo that reaches storage must carry none of it (Plan 8 S4:
// stored photos are kept up to 30 days). The fixture is a JPEG with EXIF
// (camera make, a GPS block) and a comment.

const PHOTO = join(process.cwd(), "e2e/fixtures/label-with-gps.jpg");

test("a label photo is uploaded without EXIF, GPS or comments", async ({
  page,
  context,
  request,
}) => {
  const original = readFileSync(PHOTO).toString("latin1");
  expect(original).toContain("Exif");
  expect(original).toContain("GPS");

  await request.post(`${STUB}/__reset?terms=current`);
  await signIn(context);
  await page.goto("/en/scan/label");
  await page.getByLabel("Choose a file").setInputFiles(PHOTO);

  await expect(page).toHaveURL(/\/en\/scan\/confirm\/[0-9a-f-]{36}$/);
  const { upload } = (await (await request.get(`${STUB}/__state`)).json()) as {
    upload: {
      size: number;
      jpeg: boolean;
      exif: boolean;
      gps: boolean;
      comment: boolean;
    } | null;
  };
  expect(upload).not.toBeNull();
  expect(upload).toMatchObject({
    jpeg: true,
    exif: false,
    gps: false,
    comment: false,
  });
  expect(upload?.size).toBeGreaterThan(1000);
});
