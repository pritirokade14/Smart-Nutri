import { describe, expect, it } from "vitest";
import { DIRECTION_FOR_GOAL } from "@/features/targets/lib/directionDefaults";
import { directionDefaultsFixture } from "../../support/targets-fixtures";

describe("DIRECTION_FOR_GOAL", () => {
  it("equals the shared fixture", () => {
    expect(DIRECTION_FOR_GOAL).toEqual(directionDefaultsFixture());
  });
});
