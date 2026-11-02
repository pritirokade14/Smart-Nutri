import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { components } from "@smartnutri/api-client";

export type PublicProductOut = components["schemas"]["PublicProductOut"];

const DIR = join(
  process.cwd(),
  "../../packages/test-fixtures/responses/public",
);

/** Shared public-product responses (Task 5); [] until that folder exists. */
export function publicFixtures(): { name: string; data: PublicProductOut }[] {
  if (!existsSync(DIR)) return [];
  return readdirSync(DIR)
    .filter((f) => f.endsWith(".json"))
    .sort()
    .map((f) => ({
      name: f,
      data: JSON.parse(readFileSync(join(DIR, f), "utf8")) as PublicProductOut,
    }));
}

const nutrients = {
  carbs_g: 60,
  energy_kcal: 480,
  fat_g: 20,
  fiber_g: 2,
  protein_g: 6,
  salt_g: 1.6,
  sat_fat_g: 9,
  sodium_mg: 640,
  sugars_g: 30,
};

export const offProduct: PublicProductOut = {
  product: {
    attribution: "openfoodfacts",
    barcode: "8901063201089",
    brand: "Parle",
    category: "biscuit",
    claims: ["no_added_sugar"],
    image_url: "https://images.openfoodfacts.org/images/products/x/front.jpg",
    ingredients: ["wheat flour", "sugar", "palm oil"],
    name: "Parle-G",
    per_100g: nutrients,
    product_id: null,
    serving_size_g: null,
    source: "openfoodfacts",
  },
  report: {
    nutriscore: {
      grade: "D",
      points: 14,
      partial: false,
      approximated: false,
      reason: null,
    },
    high_in: ["sugar", "fat"],
    claims: [
      {
        claim: "no_added_sugar",
        verdict: "contradicted",
        reason_code: "added_sugar_ingredient",
        params: { ingredients: ["sugar"] },
      },
    ],
  },
  score_label: "calculated_by_smartnutri",
};

export const ownProduct: PublicProductOut = {
  product: {
    ...offProduct.product,
    attribution: null,
    source: "smartnutri",
    product_id: "6b2f6c2a-0000-4000-8000-000000000001",
    image_url: null,
    ingredients: [],
    claims: [],
    name: "House Muesli",
  },
  report: {
    nutriscore: {
      grade: null,
      points: null,
      partial: false,
      approximated: false,
      reason: "insufficient_data",
    },
    high_in: [],
    claims: [],
  },
  score_label: "calculated_by_smartnutri",
};
