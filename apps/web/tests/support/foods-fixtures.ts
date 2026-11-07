import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { FoodDetailOut, FoodHit } from "@/features/foods/api/foods";

const FIXTURES = join(process.cwd(), "../../packages/test-fixtures");
const read = <T>(rel: string): T =>
  JSON.parse(readFileSync(join(FIXTURES, rel), "utf8")) as T;

type UnitCase = {
  case: string;
  per_100: FoodDetailOut["per_100"];
  quantity: number;
  unit: string;
  expected: { grams_per_unit: number | null };
};
/** A shared units/conversions.json case. */
export function unitCase(name: string): UnitCase {
  const hit = read<{ cases: UnitCase[] }>("units/conversions.json").cases.find(
    (c) => c.case === name,
  );
  if (!hit) throw new Error(`no fixture case ${name}`);
  return hit;
}

export const DAL_ID = "f0000000-0000-4000-8000-000000000001";
export const ROTI_ID = "f0000000-0000-4000-8000-000000000002";
export const DISH_ID = "f0000000-0000-4000-8000-000000000003";

/** Cooked toor dal: nutrients from the shared katori fixture, katori 142 g. */
export function dalDetail(edit?: (d: FoodDetailOut) => void): FoodDetailOut {
  const c = unitCase("katori_cooked_dal");
  const d: FoodDetailOut = {
    kind: "food",
    id: DAL_ID,
    name: "Toor dal, cooked",
    brand: null,
    basis: "g",
    per_100: c.per_100,
    units: [
      {
        code: "g",
        kind: "mass",
        ml: null,
        grams_per_unit: 1,
        source: "mass",
        user_override: false,
      },
      {
        code: "katori",
        kind: "volume",
        ml: 200,
        grams_per_unit: 142,
        source: "density",
        user_override: false,
      },
      {
        code: "katori_medium",
        kind: "volume",
        ml: 155,
        grams_per_unit: 110.05,
        source: "density",
        user_override: false,
      },
    ],
    default_unit: "katori",
    settable_units: ["piece"],
    serving_g: null,
    attribution: "attribution.usda_fdc",
    attributions: ["attribution.usda_fdc"],
    licence: null,
    dish: null,
    review_pending: true,
    numbers_hidden: { energy: false, macros: false },
  };
  edit?.(d);
  return d;
}

export const DAL_HIT: FoodHit = {
  kind: "food",
  id: DAL_ID,
  name: "Toor dal, cooked",
  brand: null,
  group: "indian",
  is_dish: false,
  grade: null,
  attribution: "attribution.usda_fdc",
  attributions: ["attribution.usda_fdc"],
};
export const ROTI_HIT: FoodHit = {
  kind: "product",
  id: ROTI_ID,
  name: "Whole wheat roti",
  brand: "Acme",
  group: "packaged",
  is_dish: false,
  grade: null,
  attribution: null,
  attributions: [],
};
export const DISH_HIT: FoodHit = {
  ...DAL_HIT,
  id: DISH_ID,
  name: "Dal tadka",
  is_dish: true,
  attribution: "attribution.smartnutri_recipe",
  attributions: ["attribution.smartnutri_recipe", "attribution.usda_fdc"],
};
