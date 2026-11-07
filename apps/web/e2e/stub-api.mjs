// Minimal stand-ins for the API and Supabase Auth in e2e runs (server-side
// fetches can't be mocked by page.route). Everything here is canned fixture
// data: the stub never decides a verdict, it serves the golden responses from
// packages/test-fixtures.
import { readFileSync } from "node:fs";
import { createServer } from "node:http";

const port = Number(process.env.STUB_API_PORT ?? 18000);
const authPort = Number(process.env.STUB_AUTH_PORT ?? 54321);
const fixtures = new URL("../../../packages/test-fixtures/", import.meta.url);
const read = (p) => JSON.parse(readFileSync(new URL(p, fixtures), "utf8"));

const body = {
  product: {
    attribution: "openfoodfacts",
    barcode: "8901063201089",
    brand: "Parle",
    category: "biscuit",
    claims: [],
    image_url: "https://images.openfoodfacts.org/images/products/x/front.jpg",
    ingredients: ["wheat flour", "sugar"],
    name: "Parle-G",
    per_100g: {},
    product_id: null,
    serving_size_g: null,
    source: "openfoodfacts",
  },
  report: {
    nutriscore: { grade: "D" },
    high_in: ["sugar"],
    claims: [],
  },
  score_label: "calculated_by_smartnutri",
};

// ---- Signed-in flows (e2e/family-verdict.spec.ts) --------------------------

export const E2E_USER_ID = "5f0c3a52-6f1e-4c9b-9d1a-2b7e8c4d1a01";
const CONSENT_VERSION = "2026-11-01";
const OLD_CONSENT_VERSION = "2026-01-01";
const PURPOSES = ["terms", "health_data", "ai_processing"];
const HEALTH = ["allergens", "conditions", "goal", "height_cm", "weight_kg"];
const index = read("responses/index.json");
const goldenVerdict = (product, member) => {
  const id = index.members[member];
  return read(`responses/analyze/${product}.json`).verdicts.find(
    (v) => v.member_id === id,
  );
};

let state;
// POST /__reset?terms=current|old&health_data=current&delete_fails=N&user_types=unanswered|<a,b>&diary=<golden day stem>
// seeds the signed-in state: terms agreed now or at an older text version
// (needs_update), how many DELETE /v1/me calls answer 503
// deletion_incomplete before one succeeds, and the account's user types
// (default: answered with "Skip for now", so other specs land on Home).
function reset(params = new URLSearchParams()) {
  const terms = params.get("terms");
  const userTypes = params.get("user_types");
  state = {
    userTypes:
      userTypes === "unanswered"
        ? null
        : {
            types: userTypes ? userTypes.split(",") : [],
            follow_ups: {},
            active_type: null,
          },
    seq: 0,
    scans: 0,
    meals: [],
    // Custom foods and recipes (Plan 12 slice 4).
    customFoods: [],
    recipes: [],
    // Favourites (Plan 12 slice 5): foods and saved meals, newest first.
    favourites: [],
    timezone: "Asia/Kolkata",
    // The meal slots (the four defaults at first); archived ones stay.
    slots: defaultSlots(),
    // Days marked as partly logged (date -> true).
    partial: {},
    // ?diary=<stem> serves that golden day (and its week) as-is.
    diaryDay: params.get("diary")
      ? read(`diary/expected/${params.get("diary")}.json`)
      : null,
    diaryWeek: params.get("diary")
      ? read(
          `diary/expected/${params.get("diary") === "day_hide_all" ? "week_hide_all" : "week_mixed"}.json`,
        )
      : null,
    // The stored daily-guide settings (GoalSettingsOut), or null.
    goal: null,
    deleteFails: Number(params.get("delete_fails") ?? 0),
    deleted: false,
    // What the browser PUT to "storage": only facts about the bytes.
    upload: null,
    consents: {
      ...Object.fromEntries(PURPOSES.map((p) => [p, null])),
      terms:
        terms === "current"
          ? CONSENT_VERSION
          : terms === "old"
            ? OLD_CONSENT_VERSION
            : null,
      health_data:
        params.get("health_data") === "current" ? CONSENT_VERSION : null,
    },
    members: [
      {
        id: "a0000000-0000-4000-8000-000000000001",
        name: "",
        relation: "self",
        birth_year: null,
        sex: null,
        height_cm: null,
        weight_kg: null,
        body_fat_pct: null,
        diet: "non_veg",
        allergens: [],
        conditions: [],
        custom_alerts: [],
        goal: null,
        is_primary: true,
      },
    ],
  };
}

const consentStates = () =>
  PURPOSES.map((purpose) => ({
    purpose,
    granted: state.consents[purpose] !== null,
    version: state.consents[purpose],
    current_version: CONSENT_VERSION,
    needs_update:
      state.consents[purpose] !== null &&
      state.consents[purpose] !== CONSENT_VERSION,
  }));

// The route gate (ruling G1): analyze, scans, meals and product create need
// `terms` at the current version.
const termsMissing = () => state.consents.terms !== CONSENT_VERSION;

const envelope = (code, details = {}) => ({
  error: { code, message_key: `error.${code}`, details },
});

const writesHealth = (b) =>
  HEALTH.some((f) => {
    const v = b[f];
    return Array.isArray(v) ? v.length > 0 : v !== null && v !== undefined;
  });

// Canned verdicts for the sugar-free biscuit: the golden diabetic_adult
// verdict for a member with diabetes, the golden no_age verdict otherwise.
function analyze() {
  const golden = read("responses/analyze/sf_biscuit.json");
  golden.verdicts = state.members.map((m) => {
    const fixture = m.conditions.includes("diabetes")
      ? "diabetic_adult"
      : "no_age";
    return {
      ...goldenVerdict("sf_biscuit", fixture),
      member_id: m.id,
      member_name: m.name,
      relation: m.relation,
      is_primary: m.is_primary,
    };
  });
  return golden;
}

// ---- User types (e2e/user-types.spec.ts) -----------------------------------
// The API's pre-fill table (Plan 9 Task 2), canned for the stub: suggestions
// only add, never remove, never relax a diet, primary member only. The stub
// never applies them; the browser PATCHes the member after the user confirms.

const PRIORITY = [
  "allergy_diet",
  "health_condition",
  "family",
  "weight_loss",
  "gym",
  "eat_better",
];
const HEALTH_TYPES = ["health_condition", "weight_loss", "allergy_diet"];
const HEALTH_FOLLOW_UPS = ["conditions", "allergens", "diet"];
const GYM_GOAL = {
  build_muscle: "build_muscle",
  lose_fat: "weight_loss",
  stay_fit: "healthy_eating",
};

function suggestPrefill(types, f, m) {
  const changes = [];
  const union = (field, chosen, reason) => {
    const added = (chosen ?? []).filter((v) => !m[field].includes(v));
    if (added.length)
      changes.push({
        field,
        current: m[field],
        value: [...m[field], ...added],
        added,
        reason,
      });
  };
  const goal = (value, reason) => {
    if (m.goal !== value)
      changes.push({
        field: "goal",
        current: m.goal,
        value,
        added: [],
        reason,
      });
  };
  if (types.includes("health_condition"))
    union("conditions", f.conditions, "health_condition");
  if (types.includes("allergy_diet")) {
    union("allergens", f.allergens, "allergy_diet");
    if (f.diet && m.diet === "non_veg" && f.diet !== "non_veg")
      changes.push({
        field: "diet",
        current: m.diet,
        value: f.diet,
        added: [],
        reason: "allergy_diet",
      });
  }
  let goalChoice = null;
  const gymGoal = types.includes("gym") ? GYM_GOAL[f.gym_goal] : undefined;
  if (types.includes("weight_loss") && gymGoal === "build_muscle")
    goalChoice = ["weight_loss", "build_muscle"];
  else if (types.includes("weight_loss")) goal("weight_loss", "weight_loss");
  else if (gymGoal) goal(gymGoal, "gym");
  if (types.includes("eat_better")) {
    union("custom_alerts", f.alerts, "eat_better");
    if (m.goal === null && !changes.some((c) => c.field === "goal"))
      goal("healthy_eating", "eat_better");
  }
  return { changes, goalChoice };
}

function userTypesOut() {
  const row = state.userTypes;
  if (!row)
    return {
      types: [],
      follow_ups: {},
      active_type: "eat_better",
      answered: false,
      answered_at: null,
      prefill: null,
    };
  const primary = state.members.find((m) => m.is_primary);
  const { changes, goalChoice } = suggestPrefill(
    row.types,
    row.follow_ups,
    primary,
  );
  return {
    types: row.types,
    follow_ups: row.follow_ups,
    active_type:
      row.active_type && row.types.includes(row.active_type)
        ? row.active_type
        : (PRIORITY.find((t) => row.types.includes(t)) ?? "eat_better"),
    answered: true,
    answered_at: "2026-11-04T00:00:00Z",
    prefill: {
      member_id: primary.id,
      changes,
      goal_choice: goalChoice,
      needs_health_consent:
        changes.length > 0 && state.consents.health_data === null,
    },
  };
}

function putUserTypes(b) {
  const f = b.follow_ups ?? {};
  const health =
    b.types.some((t) => HEALTH_TYPES.includes(t)) ||
    HEALTH_FOLLOW_UPS.some((k) => f[k] != null);
  if (health && state.consents.health_data === null)
    return [403, envelope("consent_required", { purposes: ["health_data"] })];
  const keep = state.userTypes?.active_type;
  state.userTypes = {
    types: b.types,
    follow_ups: f,
    active_type: keep && b.types.includes(keep) ? keep : null,
  };
  return [200, userTypesOut()];
}

function setActive(b) {
  if (!state.userTypes) return [404, envelope("user_types_not_found")];
  const ok =
    state.userTypes.types.includes(b.active_type) ||
    (state.userTypes.types.length === 0 && b.active_type === "eat_better");
  if (!ok) return [422, envelope("user_type_not_selected")];
  state.userTypes.active_type = b.active_type;
  return [200, userTypesOut()];
}

// ---- Meal logs (e2e/log-and-share.spec.ts) ---------------------------------
// Snapshots are per_100g x grams / 100 from the golden product (the API's
// arithmetic, canned). The stub never decides a band: every band is
// "unknown" and the limits are the week_family fixture's, as served.

const SF = read("responses/analyze/sf_biscuit.json").product;
// ---- Foods (Plan 12 slice 3): per-100 numbers and unit weights come from the
// shared units/conversions.json fixture; the stub only serves them.
const UNIT_CASES = read("units/conversions.json").cases;
const unitCase = (name) => UNIT_CASES.find((c) => c.case === name);
const ROTI_ID = "f0000000-0000-4000-8000-000000000002";
const DAL_ID = "f0000000-0000-4000-8000-000000000001";
const massUnit = {
  code: "g",
  kind: "mass",
  ml: null,
  grams_per_unit: 1,
  source: "mass",
  user_override: false,
};
const FOODS = {
  [`product:${ROTI_ID}`]: {
    kind: "product",
    id: ROTI_ID,
    name: "Whole wheat roti",
    brand: "Acme",
    basis: "g",
    per_100: unitCase("two_packaged_roti").per_100,
    units: [
      massUnit,
      {
        code: "roti",
        kind: "count",
        ml: null,
        grams_per_unit: 68,
        source: "portion_global",
        user_override: false,
      },
    ],
    default_unit: "roti",
    settable_units: [],
    serving_g: null,
    attribution: null,
    attributions: [],
    licence: null,
    dish: null,
    review_pending: false,
  },
  [`food:${DAL_ID}`]: {
    kind: "food",
    id: DAL_ID,
    name: "Toor dal, cooked",
    brand: null,
    basis: "g",
    per_100: unitCase("katori_cooked_dal").per_100,
    units: [
      massUnit,
      {
        code: "katori",
        kind: "volume",
        ml: 200,
        grams_per_unit: 142,
        source: "density",
        user_override: false,
      },
    ],
    default_unit: "katori",
    settable_units: [],
    serving_g: null,
    attribution: "attribution.usda_fdc",
    attributions: ["attribution.usda_fdc"],
    licence: null,
    dish: null,
    review_pending: true,
  },
};
const foodHit = (f) => ({
  kind: f.kind,
  id: f.id,
  name: f.name,
  brand: f.brand,
  group: f.kind === "food" ? "indian" : "packaged",
  is_dish: false,
  grade: null,
  attribution: f.attribution,
  attributions: f.attributions,
});

// ---- Custom foods and recipes (Plan 12 slice 4) ----------------------------
// The stub only does the API's arithmetic on what was typed: values per 100
// (or per serving, scaled), recipe sums of the KNOWN ingredients, and an
// "at least" list for a nutrient any ingredient did not give.
const CUSTOM_KEYS = [
  "energy_kcal",
  "protein_g",
  "carbs_g",
  "fat_g",
  "sugars_g",
  "sat_fat_g",
  "fibre_g",
  "salt_g",
];
const uuid = (n) => `b0000000-0000-4000-8000-${String(n).padStart(12, "0")}`;
const nextId = () => {
  state.seq += 1;
  return uuid(state.seq);
};
const now = () => new Date().toISOString();

function customPer100(b) {
  const factor = b.values_per === "serving" ? 100 / Number(b.serving_g) : 1;
  const n = b.nutrients ?? {};
  const out = Object.fromEntries(
    CUSTOM_KEYS.map((k) => [k, n[k] == null ? null : n[k] * factor]),
  );
  if (out.salt_g == null && n.sodium_mg != null)
    out.salt_g = (n.sodium_mg * factor * 2.5) / 1000;
  return out;
}

function customOut(f) {
  return {
    id: f.id,
    name: f.name,
    brand: f.brand ?? null,
    basis: f.basis,
    per_100: f.per_100,
    entered: {
      values_per: f.values_per,
      serving_g: f.serving_g ?? null,
      nutrients: f.nutrients,
    },
    serving_g: f.serving_g ?? null,
    density_g_per_ml: f.density_g_per_ml ?? null,
    barcode: f.barcode ?? null,
    portions: f.portions ?? [],
    created_at: f.created_at,
    updated_at: f.updated_at,
  };
}

function customFoodRoutes(method, path, q, b) {
  if (path === "/v1/custom-foods" && method === "GET") {
    const limit = Number(q.get("limit") ?? 50);
    const start = Number(q.get("cursor") ?? 0);
    const rows = state.customFoods.slice(start, start + limit);
    const more = start + limit < state.customFoods.length;
    return [
      200,
      {
        items: rows.map(customOut),
        next_cursor: more ? String(start + limit) : null,
      },
    ];
  }
  const valid = () => {
    const n = b.nutrients ?? {};
    const has = [n.energy_kcal, n.protein_g, n.carbs_g, n.fat_g].some(
      (v) => v != null,
    );
    if (!has) return [422, envelope("custom_food_nutrients_empty")];
    if (Object.values(n).some((v) => v > 5000))
      return [
        422,
        envelope("implausible_value", {
          fields: Object.entries(n)
            .filter(([, v]) => v > 5000)
            .map(([k]) => `body.nutrients.${k}`),
        }),
      ];
    return null;
  };
  const build = (id, prior) => ({
    id,
    name: String(b.name).trim(),
    brand: b.brand ?? null,
    basis: b.basis,
    values_per: b.values_per,
    serving_g: b.serving_g ?? null,
    nutrients: b.nutrients ?? {},
    per_100: customPer100(b),
    density_g_per_ml: b.density_g_per_ml ?? null,
    barcode: b.barcode ?? null,
    portions: b.portions ?? [],
    client_id: b.client_id ?? prior?.client_id ?? null,
    created_at: prior?.created_at ?? now(),
    updated_at: now(),
  });
  if (path === "/v1/custom-foods" && method === "POST") {
    const prior =
      b.client_id && state.customFoods.find((f) => f.client_id === b.client_id);
    if (prior) return [200, customOut(prior)];
    const bad = valid();
    if (bad) return bad;
    const f = build(nextId());
    state.customFoods.unshift(f);
    return [201, customOut(f)];
  }
  const one = path.match(/^\/v1\/custom-foods\/([0-9a-f-]{36})$/);
  if (one) {
    const i = state.customFoods.findIndex((f) => f.id === one[1]);
    if (i < 0) return [404, envelope("custom_food_not_found")];
    if (method === "DELETE") {
      state.customFoods.splice(i, 1);
      return [204];
    }
    if (method === "PUT") {
      const bad = valid();
      if (bad) return bad;
      state.customFoods[i] = build(one[1], state.customFoods[i]);
      return [200, customOut(state.customFoods[i])];
    }
  }
  return null;
}

// How the grams came from the unit: a per-food weight or a density is
// approximate (the client shows "≈"); the rest is exact.
const unitSource = (u) =>
  u.source === "density"
    ? "density"
    : u.source === "portion_user" || u.source === "portion_global"
      ? "portion"
      : "grams";
const gramUnits = (extra = []) => [massUnit, ...extra];

// Resolve one recipe ingredient (a food or a custom food) to grams.
function ingredientRow(ing, position) {
  const food = ing.food_id
    ? FOODS[`food:${ing.food_id}`]
    : ing.custom_food_id
      ? mineFood("custom_food", ing.custom_food_id)
      : null;
  if (!food) return { error: [404, envelope("invalid_product_ref")] };
  const unit = food.units.find((u) => u.code === ing.unit);
  if (!unit)
    return {
      error: [422, envelope("unit_grams_unknown", { position })],
    };
  return {
    food,
    row: {
      position,
      source_kind: ing.food_id ? "food" : "custom_food",
      food_id: ing.food_id ?? null,
      custom_food_id: ing.custom_food_id ?? null,
      product_id: null,
      barcode: null,
      name: food.name,
      quantity: ing.quantity,
      unit: ing.unit,
      grams: round1(ing.quantity * unit.grams_per_unit),
      attribution: food.attribution ?? null,
      available: true,
    },
  };
}

function recipeOut(r) {
  const rows = r.ingredients.map((i, p) => ingredientRow(i, p));
  const resolved = rows.map((x, p) =>
    x.error
      ? {
          position: p,
          source_kind: "custom_food",
          food_id: null,
          custom_food_id: r.ingredients[p].custom_food_id ?? null,
          product_id: null,
          barcode: null,
          name: r.names[p],
          quantity: r.ingredients[p].quantity,
          unit: r.ingredients[p].unit,
          grams: 0,
          attribution: null,
          available: false,
          _per100: null,
        }
      : { ...x.row, _per100: x.food.per_100 },
  );
  const totalRaw = resolved.reduce((a, i) => a + i.grams, 0);
  const basis = r.cooked_weight_g ?? totalRaw;
  const sums = {};
  const incomplete = [];
  for (const k of CUSTOM_KEYS) {
    const vals = resolved.map((i) => (i._per100 ? i._per100[k] : null));
    const known = vals
      .map((v, p) => (v == null ? null : (v * resolved[p].grams) / 100))
      .filter((v) => v != null);
    sums[k] = known.length ? known.reduce((a, v) => a + v, 0) : null;
    if (known.length && known.length < vals.length) incomplete.push(k);
  }
  const redact = (snap) => {
    const d = display();
    return Object.fromEntries(
      Object.entries(snap).map(([k, v]) => [
        k,
        (k === "energy_kcal" ? d !== "show" : d === "hide_all") ? null : v,
      ]),
    );
  };
  const per100 = Object.fromEntries(
    CUSTOM_KEYS.map((k) => [
      k,
      sums[k] == null ? null : round1((sums[k] * 100) / basis),
    ]),
  );
  const perServing = r.servings
    ? Object.fromEntries(
        CUSTOM_KEYS.map((k) => [
          k,
          sums[k] == null ? null : round1(sums[k] / r.servings),
        ]),
      )
    : null;
  const d = display();
  return {
    id: r.id,
    name: r.name,
    servings: r.servings ?? null,
    cooked_weight_g: r.cooked_weight_g ?? null,
    total_raw_g: round1(totalRaw),
    basis_weight_g: round1(basis),
    per_100g: redact(per100),
    per_serving: perServing ? redact(perServing) : null,
    incomplete_nutrients: incomplete,
    attributions: [
      ...new Set(
        resolved.flatMap((i) => (i.attribution ? [i.attribution] : [])),
      ),
    ],
    ingredients: resolved.map(({ _per100, ...rest }) => rest),
    numbers_hidden: { energy: d !== "show", macros: d === "hide_all" },
    updated_at: r.updated_at,
    _strict: Object.fromEntries(
      CUSTOM_KEYS.map((k) => [
        k,
        incomplete.includes(k) || sums[k] == null
          ? null
          : (sums[k] * 100) / basis,
      ]),
    ),
  };
}
const publicRecipe = (r) => {
  const { _strict, ...out } = recipeOut(r);
  return out;
};

function recipeRoutes(method, path, q, b) {
  if (path === "/v1/recipes" && method === "GET") {
    const limit = Number(q.get("limit") ?? 50);
    const start = Number(q.get("cursor") ?? 0);
    const rows = state.recipes.slice(start, start + limit);
    return [
      200,
      {
        items: rows.map((r) => {
          const o = publicRecipe(r);
          return {
            id: o.id,
            name: o.name,
            servings: o.servings,
            incomplete_nutrients: o.incomplete_nutrients,
            updated_at: o.updated_at,
          };
        }),
        next_cursor:
          start + limit < state.recipes.length ? String(start + limit) : null,
      },
    ];
  }
  const parse = (prior) => {
    const ingredients = b.ingredients ?? [];
    const names = [];
    for (const [p, ing] of ingredients.entries()) {
      const x = ingredientRow(ing, p);
      if (x.error) return { error: x.error };
      names.push(x.row.name);
    }
    if (ingredients.length === 0)
      return { error: [422, envelope("validation_error")] };
    return {
      recipe: {
        id: prior?.id ?? nextId(),
        name: String(b.name).trim(),
        servings: b.servings ?? null,
        cooked_weight_g: b.cooked_weight_g ?? null,
        ingredients,
        names,
        client_id: b.client_id ?? prior?.client_id ?? null,
        updated_at: now(),
      },
    };
  };
  if (path === "/v1/recipes" && method === "POST") {
    const prior =
      b.client_id && state.recipes.find((r) => r.client_id === b.client_id);
    if (prior) return [200, publicRecipe(prior)];
    const { recipe, error } = parse();
    if (error) return error;
    state.recipes.unshift(recipe);
    return [201, publicRecipe(recipe)];
  }
  const one = path.match(/^\/v1\/recipes\/([0-9a-f-]{36})$/);
  if (one) {
    const i = state.recipes.findIndex((r) => r.id === one[1]);
    if (i < 0) return [404, envelope("recipe_not_found")];
    if (method === "GET") return [200, publicRecipe(state.recipes[i])];
    if (method === "DELETE") {
      state.recipes.splice(i, 1);
      return [204];
    }
    if (method === "PUT") {
      const { recipe, error } = parse(state.recipes[i]);
      if (error) return error;
      state.recipes[i] = recipe;
      return [200, publicRecipe(recipe)];
    }
  }
  return null;
}

// A custom food or recipe as the food detail the portion picker reads.
function mineFood(kind, id) {
  if (kind === "custom_food") {
    const f = state.customFoods.find((x) => x.id === id);
    if (!f) return null;
    return {
      kind,
      id,
      name: f.name,
      brand: f.brand ?? null,
      basis: f.basis,
      per_100: f.per_100,
      units: gramUnits([
        ...(f.serving_g
          ? [
              {
                code: "serving",
                kind: "count",
                ml: null,
                grams_per_unit: f.serving_g,
                source: "serving",
                user_override: false,
              },
            ]
          : []),
        ...(f.portions ?? []).map((p) => ({
          code: p.unit,
          kind: "count",
          ml: null,
          grams_per_unit: p.grams_per_unit,
          source: "portion_user",
          user_override: true,
        })),
      ]),
      default_unit: f.serving_g ? "serving" : "g",
      settable_units: [],
      serving_g: f.serving_g ?? null,
      attribution: null,
      attributions: [],
      licence: null,
      dish: null,
      review_pending: false,
      recipe_incomplete: [],
    };
  }
  if (kind === "recipe") {
    const r = state.recipes.find((x) => x.id === id);
    if (!r) return null;
    const { _strict, ...o } = recipeOut(r);
    const perServingG = o.servings
      ? round1(o.basis_weight_g / o.servings)
      : null;
    return {
      kind,
      id,
      name: r.name,
      brand: null,
      basis: "g",
      per_100: _strict,
      units: gramUnits(
        perServingG
          ? [
              {
                code: "serving",
                kind: "count",
                ml: null,
                grams_per_unit: perServingG,
                source: "serving",
                user_override: false,
              },
            ]
          : [],
      ),
      default_unit: perServingG ? "serving" : "g",
      settable_units: [],
      serving_g: perServingG,
      attribution: o.attributions[0] ?? null,
      attributions: o.attributions,
      licence: null,
      dish: null,
      review_pending: false,
      recipe_incomplete: o.incomplete_nutrients,
    };
  }
  return null;
}
const mineHit = (kind, f) => ({
  kind,
  id: f.id,
  name: f.name,
  brand: null,
  group: "mine",
  is_dish: false,
  grade: null,
  attribution: null,
  attributions: [],
});
const WEEK = read("meals/expected/week_family.dad_diabetic.json");
const IST_MS = 330 * 60_000;
const istDate = (iso) =>
  new Date(new Date(iso).getTime() + IST_MS).toISOString().slice(0, 10);
const addDays = (d, n) => {
  const x = new Date(`${d}T00:00:00Z`);
  x.setUTCDate(x.getUTCDate() + n);
  return x.toISOString().slice(0, 10);
};
const KEYS = ["energy_kcal", "sugars_g", "salt_g", "protein_g"];
const UNKNOWN_BANDS = {
  kcal: "unknown",
  protein_g: "unknown",
  salt_g: "unknown",
  sugar_g: "unknown",
};
const round1 = (n) => Math.round(n * 10) / 10;

const PRIMARY_ID = "a0000000-0000-4000-8000-000000000001";
const SLOT_KEYS = ["breakfast", "lunch", "snack", "dinner"];
const slotId = (i) => `d0000000-0000-4000-8000-00000000000${i + 1}`;
const defaultSlots = () =>
  SLOT_KEYS.map((k, i) => ({
    id: slotId(i),
    member_id: PRIMARY_ID,
    position: i,
    label_key: `diary.slot.${k}`,
    custom_label: null,
    default_time_window: null,
    is_default: true,
    archived: false,
  }));
const activeSlots = () =>
  state.slots
    .filter((r) => !r.archived)
    .sort((a, b) => a.position - b.position);
const slotRows = activeSlots;
// Canned: the stub's pick for the current IST hour (the real API decides).
const suggestedSlot = () => {
  const h = new Date(Date.now() + IST_MS).getUTCHours();
  const want = slotId(h >= 4 && h < 11 ? 0 : h < 16 ? 1 : h < 19 ? 2 : 3);
  const rows = activeSlots();
  return (rows.find((r) => r.id === want) ?? rows[0]).id;
};
const NUTRIENTS = [
  "energy_kcal",
  "sugars_g",
  "salt_g",
  "protein_g",
  "fat_g",
  "sat_fat_g",
  "carbs_g",
  "fibre_g",
];
const DIARY_KEYS = [
  "energy_kcal",
  "protein_g",
  "fat_g",
  "carbs_g",
  "fibre_g",
  "sugars_g",
  "salt_g",
];
const display = () => state.goal?.numbers_display ?? "show";
const nowIso = () => new Date().toISOString();
const capNow = (iso) => (new Date(iso) > new Date() ? nowIso() : iso);

// What the API returns for a stored meal: the stub's private fields are
// dropped and hidden numbers are null (the API redacts every surface).
function publicMeal(m) {
  const d = display();
  const out = Object.fromEntries(
    Object.entries(m).filter(([k]) => !k.startsWith("_")),
  );
  out.incomplete = NUTRIENTS.filter((k) => m.nutrients[k] == null);
  out.nutrients = Object.fromEntries(
    NUTRIENTS.map((k) => [
      k,
      (k === "energy_kcal" ? d !== "show" : d === "hide_all")
        ? null
        : m.nutrients[k],
    ]),
  );
  return out;
}

function scaled(per100, grams) {
  const snap = (v) => (v == null ? null : round1((v * grams) / 100));
  return Object.fromEntries(NUTRIENTS.map((k) => [k, snap(per100[k])]));
}

function logMeal(b) {
  const prior =
    b.client_id && state.meals.find((m) => m.client_id === b.client_id);
  if (prior) return [200, publicMeal(prior)];
  const memberId = b.member_id ?? PRIMARY_ID;
  if (!state.members.some((m) => m.id === memberId))
    return [404, envelope("member_not_found")];
  const today = istDate(nowIso());
  if (b.local_date && b.local_date > today)
    return [422, envelope("date_in_future")];
  if (b.meal_slot_id && !slotRows().some((r) => r.id === b.meal_slot_id))
    return [404, envelope("meal_slot_not_found")];
  state.seq += 1;
  const id = `c0000000-0000-4000-8000-${String(state.seq).padStart(12, "0")}`;
  const when = b.local_date
    ? capNow(`${b.local_date}T${istClock(nowIso())}+05:30`)
    : (b.eaten_at ?? nowIso());
  const base = {
    id,
    member_id: memberId,
    eaten_at: when,
    client_id: b.client_id ?? null,
    meal_slot_id: b.meal_slot_id ?? suggestedSlot(),
    local_date: istDate(when),
    updated_at: nowIso(),
  };
  let meal;
  if (b.quick) {
    if (!(b.quick.energy_kcal > 0))
      return [422, envelope("quick_add_energy_required")];
    meal = {
      ...base,
      product_id: null,
      barcode: null,
      product_name: b.quick.name ?? "",
      grade: null,
      grams: null,
      source_kind: "quick_add",
      attribution: null,
      nutrients: Object.fromEntries(
        NUTRIENTS.map((k) => [k, b.quick[k] ?? null]),
      ),
    };
  } else if (
    b.food_id ||
    b.custom_food_id ||
    b.recipe_id ||
    b.product_id === ROTI_ID
  ) {
    const f = b.food_id
      ? FOODS[`food:${b.food_id}`]
      : b.custom_food_id
        ? mineFood("custom_food", b.custom_food_id)
        : b.recipe_id
          ? mineFood("recipe", b.recipe_id)
          : FOODS[`product:${b.product_id}`];
    if (!f) return [404, envelope("food_not_found")];
    const u = f.units.find((x) => x.code === b.unit);
    if (!(b.quantity > 0) || !u) return [422, envelope("unit_grams_unknown")];
    const grams = round1(b.quantity * u.grams_per_unit);
    meal = {
      ...base,
      product_id: b.food_id || b.custom_food_id || b.recipe_id ? null : f.id,
      food_id: b.food_id ?? null,
      custom_food_id: b.custom_food_id ?? null,
      recipe_id: b.recipe_id ?? null,
      barcode: null,
      product_name: f.name,
      grade: null,
      grams,
      quantity: b.quantity,
      unit: b.unit,
      basis: f.basis,
      source_kind: b.food_id
        ? "food"
        : b.custom_food_id
          ? "custom_food"
          : b.recipe_id
            ? "recipe"
            : "product",
      unit_source: unitSource(u),
      _sources: Object.fromEntries(f.units.map((x) => [x.code, unitSource(x)])),
      attribution: null,
      attributions: f.attributions,
      portion_units: f.units.map((x) => ({
        code: x.code,
        grams_per_unit: x.grams_per_unit,
      })),
      nutrients: scaled(f.per_100, grams),
      _per100: f.per_100,
    };
  } else {
    if (b.product_id !== SF.product_id)
      return [404, envelope("product_not_found")];
    const grams = b.grams ?? (b.servings ?? 0) * SF.serving_size_g;
    if (!(grams > 0)) return [422, envelope("portion_required")];
    meal = {
      ...base,
      product_id: SF.product_id,
      barcode: null,
      product_name: SF.name,
      grade: "D",
      grams,
      source_kind: "product",
      attribution: null,
      nutrients: scaled(SF.per_100g, grams),
      _per100: SF.per_100g,
    };
  }
  state.meals.push(meal);
  return [201, publicMeal(meal)];
}

const istClock = (iso) =>
  new Date(new Date(iso).getTime() + IST_MS).toISOString().slice(11, 19);

function patchMeal(id, b) {
  const m = state.meals.find((x) => x.id === id);
  if (!m) return [404, envelope("meal_not_found")];
  const set = [
    "grams",
    "servings",
    "quantity",
    "meal_slot_id",
    "eaten_at",
    "quick",
  ].filter((k) => b[k] != null);
  if (!set.length) return [422, envelope("validation_error")];
  if (b.quantity != null) {
    const u = (m.portion_units ?? []).find((x) => x.code === b.unit);
    if (!u) return [422, envelope("unit_grams_unknown")];
    m.quantity = b.quantity;
    m.unit = b.unit;
    m.grams = round1(b.quantity * u.grams_per_unit);
    m.unit_source = m._sources?.[b.unit] ?? null;
    m.nutrients = scaled(m._per100, m.grams);
  }
  if (b.grams != null) {
    if (m.source_kind === "quick_add")
      return [422, envelope("validation_error")];
    m.grams = b.grams;
    m.nutrients = scaled(m._per100, b.grams);
  }
  if (b.quick != null) {
    if (m.source_kind !== "quick_add")
      return [422, envelope("validation_error")];
    m.product_name = b.quick.name ?? "";
    m.nutrients = Object.fromEntries(
      NUTRIENTS.map((k) => [k, b.quick[k] ?? null]),
    );
  }
  if (b.meal_slot_id != null) {
    const to = state.slots.find((r) => r.id === b.meal_slot_id);
    if (!to) return [404, envelope("meal_slot_not_found")];
    if (to.archived) return [422, envelope("meal_slot_archived")];
    m.meal_slot_id = b.meal_slot_id;
  }
  m.updated_at = nowIso();
  return [200, publicMeal(m)];
}

function copyMeals(b) {
  const today = istDate(nowIso());
  if (b.from_date > today || b.to_date > today)
    return [422, envelope("date_in_future")];
  const source = state.meals
    .filter(
      (m) =>
        m.member_id === (b.member_id ?? PRIMARY_ID) &&
        m.local_date === b.from_date &&
        (!b.from_slot_id || m.meal_slot_id === b.from_slot_id),
    )
    .sort((x, y) => x.eaten_at.localeCompare(y.eaten_at));
  if (!source.length) return [422, envelope("copy_source_empty")];
  const created = [];
  let fresh = false;
  for (const src of source) {
    const cid = `${b.client_id}:${src.id}`;
    let copy = state.meals.find((m) => m.client_id === cid);
    if (!copy) {
      fresh = true;
      state.seq += 1;
      copy = {
        ...src,
        id: `c0000000-0000-4000-8000-${String(state.seq).padStart(12, "0")}`,
        client_id: cid,
        meal_slot_id: b.to_slot_id ?? src.meal_slot_id,
        eaten_at: capNow(`${b.to_date}T${istClock(src.eaten_at)}+05:30`),
        local_date: b.to_date,
        updated_at: nowIso(),
      };
      state.meals.push(copy);
    }
    created.push(publicMeal(copy));
  }
  return [fresh ? 201 : 200, { created }];
}

// ---- Favourites (e2e/diary-favourites.spec.ts) ------------------------------
// A food favourite points at a food; a meal favourite keeps a snapshot of the
// source entries (private `_entries`). No nutrient value is ever returned.

const favRefOf = (b) =>
  b.food_id
    ? ["food", "food_id", b.food_id]
    : b.custom_food_id
      ? ["custom_food", "custom_food_id", b.custom_food_id]
      : b.recipe_id
        ? ["recipe", "recipe_id", b.recipe_id]
        : b.product_id
          ? ["product", "product_id", b.product_id]
          : ["off", "barcode", b.barcode];

const publicFav = ({ _entries, ...f }) => f;

function favouriteRoutes(method, path, b) {
  if (method === "GET" && path === "/v1/favourites")
    return [200, { items: state.favourites.map(publicFav) }];
  if (method === "POST" && path === "/v1/favourites") {
    const [kind, key, id] = favRefOf(b);
    const prior = state.favourites.find(
      (f) => f.kind === "food" && f[key] === id,
    );
    if (prior) return [200, publicFav(prior)];
    const f =
      kind === "food"
        ? FOODS[`food:${id}`]
        : kind === "product"
          ? FOODS[`product:${id}`]
          : mineFood(kind, id);
    if (!f) return [404, envelope("food_not_found")];
    if (f.retired) return [422, envelope("food_retired")];
    if (state.favourites.length >= 200)
      return [422, envelope("favourite_limit")];
    if (b.default_unit && !f.units.some((u) => u.code === b.default_unit))
      return [422, envelope("unit_grams_unknown")];
    state.seq += 1;
    const fav = {
      id: `e0000000-0000-4000-8000-${String(state.seq).padStart(12, "0")}`,
      member_id: b.member_id ?? PRIMARY_ID,
      kind: "food",
      source_kind: kind,
      product_id: null,
      barcode: null,
      food_id: null,
      custom_food_id: null,
      recipe_id: null,
      [key]: id,
      name: f.name,
      default_quantity: b.default_quantity ?? null,
      default_unit: b.default_unit ?? null,
      item_count: 1,
      items: null,
      attributions: f.attributions ?? [],
      created_at: nowIso(),
    };
    state.favourites.unshift(fav);
    return [201, publicFav(fav)];
  }
  if (method === "POST" && path === "/v1/favourites/meals") {
    const prior = b.client_id
      ? state.favourites.find((f) => f._clientId === b.client_id)
      : null;
    if (prior) return [200, publicFav(prior)];
    const len = [...(b.name ?? "")].length;
    if (!b.name || b.name.trim() === "" || len > 40)
      return [422, envelope("validation_error")];
    if (b.from_date > istDate(nowIso()))
      return [422, envelope("date_in_future")];
    if (!slotRows().some((r) => r.id === b.from_slot_id))
      return [404, envelope("meal_slot_not_found")];
    const entries = state.meals
      .filter(
        (m) =>
          m.member_id === (b.member_id ?? PRIMARY_ID) &&
          m.local_date === b.from_date &&
          m.meal_slot_id === b.from_slot_id,
      )
      .sort((x, y) => x.eaten_at.localeCompare(y.eaten_at));
    if (!entries.length) return [422, envelope("copy_source_empty")];
    if (state.favourites.length >= 200)
      return [422, envelope("favourite_limit")];
    state.seq += 1;
    const fav = {
      id: `e0000000-0000-4000-8000-${String(state.seq).padStart(12, "0")}`,
      member_id: b.member_id ?? PRIMARY_ID,
      kind: "meal",
      source_kind: null,
      product_id: null,
      barcode: null,
      food_id: null,
      custom_food_id: null,
      recipe_id: null,
      name: b.name,
      default_quantity: null,
      default_unit: null,
      item_count: entries.length,
      items: entries.map((m) => ({
        name: m.product_name,
        quantity: m.quantity ?? null,
        unit: m.unit ?? null,
        grams: m.grams ?? null,
        source_kind: m.source_kind,
        attributions: m.attributions ?? [],
      })),
      attributions: [...new Set(entries.flatMap((m) => m.attributions ?? []))],
      created_at: nowIso(),
      _entries: entries.map((m) => structuredClone(m)),
      _clientId: b.client_id ?? null,
    };
    state.favourites.unshift(fav);
    return [201, publicFav(fav)];
  }
  const one = path.match(/^\/v1\/favourites\/([^/]+)(\/log)?$/);
  if (!one) return null;
  const idx = state.favourites.findIndex((f) => f.id === one[1]);
  if (idx < 0) return [404, envelope("favourite_not_found")];
  if (method === "DELETE" && !one[2]) {
    state.favourites.splice(idx, 1);
    return [204];
  }
  if (method === "POST" && one[2]) {
    const fav = state.favourites[idx];
    if (fav.kind !== "meal") return [422, envelope("validation_error")];
    const today = istDate(nowIso());
    const day = b.local_date ?? today;
    if (day > today) return [422, envelope("date_in_future")];
    if (b.meal_slot_id && !slotRows().some((r) => r.id === b.meal_slot_id))
      return [404, envelope("meal_slot_not_found")];
    const created = [];
    let fresh = false;
    for (const src of fav._entries) {
      const cid = `${b.client_id}:${src.id}`;
      let copy = state.meals.find((m) => m.client_id === cid);
      if (!copy) {
        fresh = true;
        state.seq += 1;
        copy = {
          ...structuredClone(src),
          id: `c0000000-0000-4000-8000-${String(state.seq).padStart(12, "0")}`,
          client_id: cid,
          meal_slot_id: b.meal_slot_id ?? suggestedSlot(),
          eaten_at: capNow(`${day}T${istClock(src.eaten_at)}+05:30`),
          local_date: day,
          updated_at: nowIso(),
        };
        state.meals.push(copy);
      }
      created.push(publicMeal(copy));
    }
    return [fresh ? 201 : 200, { created }];
  }
  return null;
}

// ---- Diary (e2e/diary.spec.ts) ----------------------------------------------
// With ?diary=<stem> on /__reset the golden day (and week) is served as-is.
// Otherwise a day is assembled from the stored meals: sums of the known
// values only (null when none is known), never a verdict. Targets, when a
// guide exists, are the golden TargetsOut; `remaining` and `progress` are the
// stub's own arithmetic, only to exercise the screen.

const sumKnown = (list, k) => {
  const known = list.map((m) => m.nutrients[k]).filter((v) => v != null);
  return known.length ? round1(known.reduce((a, v) => a + v, 0)) : null;
};
const totalsOf = (list) =>
  Object.fromEntries(DIARY_KEYS.map((k) => [k, sumKnown(list, k)]));
const incompleteOf = (list) =>
  Object.fromEntries(
    DIARY_KEYS.map((k) => [k, list.some((m) => m.nutrients[k] == null)]),
  );
const redactTotals = (t) => {
  const d = display();
  return Object.fromEntries(
    DIARY_KEYS.map((k) => [
      k,
      (k === "energy_kcal" ? d !== "show" : d === "hide_all") ? null : t[k],
    ]),
  );
};

// Meal slots (Plan 11 slice 2b): create (max 6 active), rename, reorder and
// archive/delete, with the API's error codes. Labels are stored as typed.
const SLOT_MAX = 6;
const labelOk = (v) =>
  typeof v === "string" &&
  [...v.trim()].length >= 1 &&
  [...v.trim()].length <= 30;
function mealSlotRoute(method, path, b) {
  const active = activeSlots();
  const dup = (label, exceptId) =>
    active.some(
      (r) =>
        r.id !== exceptId &&
        r.custom_label != null &&
        r.custom_label.toLowerCase() === label.toLowerCase(),
    );
  if (method === "POST" && path === "/v1/meal-slots") {
    if (!labelOk(b.custom_label)) return [422, envelope("validation_error")];
    const label = b.custom_label.trim();
    if (b.client_id) {
      const prior = state.slots.find((r) => r.client_id === b.client_id);
      if (prior) return [200, publicSlot(prior)];
    }
    if (active.length >= SLOT_MAX)
      return [422, envelope("meal_slot_limit_reached", { max: SLOT_MAX })];
    if (dup(label)) return [422, envelope("meal_slot_label_duplicate")];
    const n = state.slots.length + 1;
    const row = {
      id: `d0000000-0000-4000-8000-${String(100 + n).padStart(12, "0")}`,
      member_id: PRIMARY_ID,
      position: Math.max(-1, ...state.slots.map((r) => r.position)) + 1,
      label_key: null,
      custom_label: label,
      default_time_window: b.default_time_window ?? null,
      is_default: false,
      archived: false,
      client_id: b.client_id ?? null,
    };
    state.slots.push(row);
    return [201, publicSlot(row)];
  }
  if (method === "PUT" && path === "/v1/meal-slots/order") {
    const ids = b.ids ?? [];
    const unknown = ids.find((i) => !state.slots.some((r) => r.id === i));
    if (unknown) return [404, envelope("meal_slot_not_found")];
    if (
      ids.length !== active.length ||
      new Set(ids).size !== ids.length ||
      !active.every((r) => ids.includes(r.id))
    )
      return [422, envelope("validation_error")];
    ids.forEach((id, i) => {
      state.slots.find((r) => r.id === id).position = i;
    });
    return [200, { items: activeSlots().map(publicSlot) }];
  }
  const one = path.match(/^\/v1\/meal-slots\/([0-9a-f-]{36})$/);
  if (!one) return null;
  const row = state.slots.find((r) => r.id === one[1]);
  if (!row) return [404, envelope("meal_slot_not_found")];
  if (method === "PATCH") {
    if (row.archived) return [422, envelope("meal_slot_archived")];
    if (b.clear_custom_label && row.is_default) row.custom_label = null;
    if (b.custom_label != null) {
      if (!labelOk(b.custom_label)) return [422, envelope("validation_error")];
      const label = b.custom_label.trim();
      if (dup(label, row.id))
        return [422, envelope("meal_slot_label_duplicate")];
      row.custom_label = label;
    }
    if (b.clear_time_window) row.default_time_window = null;
    if (b.default_time_window) row.default_time_window = b.default_time_window;
    return [200, publicSlot(row)];
  }
  if (method === "DELETE") {
    if (row.archived) return [200, { result: "archived" }];
    if (active.length <= 1) return [422, envelope("meal_slot_last_active")];
    const used = state.meals.some((m) => m.meal_slot_id === row.id);
    if (used || row.is_default) {
      row.archived = true;
      return [200, { result: "archived" }];
    }
    state.slots = state.slots.filter((r) => r.id !== row.id);
    return [200, { result: "deleted" }];
  }
  return null;
}
const publicSlot = ({ client_id: _c, ...r }) => r;

function diaryDayOut(date) {
  if (state.diaryDay && !date) return [200, state.diaryDay];
  const today = istDate(nowIso());
  const day = date ?? today;
  if (day > today) return [422, envelope("date_in_future")];
  const d = display();
  const hidden = { energy: d !== "show", macros: d === "hide_all" };
  const dayMeals = state.meals
    .filter((m) => m.member_id === PRIMARY_ID && m.local_date === day)
    .sort((x, y) => x.eaten_at.localeCompare(y.eaten_at));
  const consent = state.consents.health_data === null;
  let targets = null;
  let status = "consent_required";
  if (!consent) {
    const [, t] = targetsRoute("GET", "/v1/targets", {});
    targets = t;
    status = t.status;
  }
  const eaten = totalsOf(dayMeals);
  const incomplete = incompleteOf(dayMeals);
  const TARGET = {
    energy_kcal: targets?.energy_kcal,
    protein_g: targets?.protein_g,
    fat_g: targets?.fat_g,
    carbs_g: targets?.carbs_g,
  };
  const MACRO4 = ["energy_kcal", "protein_g", "fat_g", "carbs_g"];
  const ready = status === "ready";
  const remaining = ready
    ? Object.fromEntries(
        MACRO4.map((k) => [
          k,
          incomplete[k] || (k === "energy_kcal" ? hidden.energy : hidden.macros)
            ? null
            : round1(TARGET[k] - (eaten[k] ?? 0)),
        ]),
      )
    : null;
  const progress = ready
    ? Object.fromEntries(
        MACRO4.map((k) => [
          k,
          incomplete[k]
            ? null
            : TARGET[k]
              ? Math.round(((eaten[k] ?? 0) / TARGET[k]) * 100) / 100
              : 0.5,
        ]),
      )
    : null;
  return [
    200,
    {
      member_id: PRIMARY_ID,
      date: day,
      today,
      timezone: "Asia/Kolkata",
      slots: state.slots
        .filter(
          (r) => !r.archived || dayMeals.some((m) => m.meal_slot_id === r.id),
        )
        .sort((a, b) => a.position - b.position)
        .map((r) => {
          const list = dayMeals.filter((m) => m.meal_slot_id === r.id);
          return {
            slot_id: r.id,
            label_key: r.label_key,
            custom_label: r.custom_label,
            position: r.position,
            archived: r.archived,
            entries: list.map(publicMeal),
            totals: redactTotals(totalsOf(list)),
            incomplete: incompleteOf(list),
          };
        }),
      totals: redactTotals(eaten),
      incomplete,
      targets,
      targets_status: status,
      remaining,
      progress,
      limits_bands: UNKNOWN_BANDS,
      partial_logged: Boolean(state.partial[day]),
      numbers_hidden: hidden,
      pending_clinician_review: true,
    },
  ];
}

function diaryWeekOut(end) {
  if (state.diaryWeek && !end) return [200, state.diaryWeek];
  const today = istDate(nowIso());
  const last = end ?? today;
  if (last > today) return [422, envelope("date_in_future")];
  const days = Array.from({ length: 7 }, (_, i) => {
    const date = addDays(last, i - 6);
    const list = state.meals.filter(
      (m) => m.member_id === PRIMARY_ID && m.local_date === date,
    );
    return {
      date,
      items: list.length,
      totals: redactTotals(totalsOf(list)),
      incomplete: incompleteOf(list),
      targets: null,
      progress: null,
      partial_logged: Boolean(state.partial[date]),
      bands: UNKNOWN_BANDS,
    };
  });
  const averaged = days.filter((d) => d.items > 0 && !d.partial_logged);
  const avg = (k) => {
    const known = averaged.map((d) => d.totals[k]).filter((v) => v != null);
    return known.length
      ? round1(known.reduce((a, v) => a + v, 0) / averaged.length)
      : null;
  };
  const d = display();
  return [
    200,
    {
      member_id: PRIMARY_ID,
      start: days[0].date,
      end: last,
      today,
      days,
      averages: {
        energy_kcal: avg("energy_kcal"),
        protein_g: avg("protein_g"),
        fat_g: avg("fat_g"),
        carbs_g: avg("carbs_g"),
      },
      averages_incomplete: Object.fromEntries(
        DIARY_KEYS.map((k) => [k, averaged.some((day) => day.incomplete[k])]),
      ),
      averaged_days: averaged.length,
      protein_met_days: 0,
      numbers_hidden: { energy: d !== "show", macros: d === "hide_all" },
      pending_clinician_review: true,
    },
  ];
}

function diaryRecents() {
  const seen = new Set();
  const items = [];
  for (const m of [...state.meals].reverse()) {
    if (m.source_kind === "quick_add") continue;
    const ref = m.food_id ?? m.custom_food_id ?? m.recipe_id ?? m.product_id;
    if (seen.has(ref)) continue;
    seen.add(ref);
    const refKey = m.food_id
      ? "food_id"
      : m.custom_food_id
        ? "custom_food_id"
        : m.recipe_id
          ? "recipe_id"
          : "product_id";
    items.push({
      favourite_id:
        state.favourites.find((f) => f.kind === "food" && f[refKey] === ref)
          ?.id ?? null,
      source_kind: m.source_kind,
      product_id: m.product_id,
      food_id: m.food_id ?? null,
      custom_food_id: m.custom_food_id ?? null,
      recipe_id: m.recipe_id ?? null,
      basis: m.basis ?? "g",
      unit_source: m.unit_source ?? null,
      quantity: m.quantity ?? null,
      unit: m.unit ?? null,
      attributions: m.attributions ?? [],
      barcode: null,
      name: m.product_name,
      grade: m.grade,
      grams: m.grams,
      meal_slot_id: m.meal_slot_id,
      last_eaten_at: m.eaten_at,
      attribution: null,
    });
  }
  return [200, { items }];
}

function dayOf(memberId, date) {
  const meals = state.meals.filter(
    (m) => m.member_id === memberId && istDate(m.eaten_at) === date,
  );
  const totals = Object.fromEntries(
    KEYS.map((k) => {
      const known = meals.map((m) => m.nutrients[k]).filter((v) => v != null);
      return [
        k,
        known.length ? round1(known.reduce((a, v) => a + v, 0)) : null,
      ];
    }),
  );
  const incomplete = Object.fromEntries(
    KEYS.map((k) => [k, meals.some((m) => m.nutrients[k] == null)]),
  );
  return {
    date,
    items: meals.length,
    totals,
    incomplete,
    bands: UNKNOWN_BANDS,
  };
}

function summary(q) {
  const memberId = q.get("member_id");
  if (!state.members.some((m) => m.id === memberId))
    return [404, envelope("member_not_found")];
  const end = q.get("date") ?? istDate(new Date().toISOString());
  const n = q.get("period") === "week" ? 7 : 1;
  const days = Array.from({ length: n }, (_, i) =>
    dayOf(memberId, addDays(end, i - n + 1)),
  );
  const totals = Object.fromEntries(
    KEYS.map((k) => {
      const known = days.map((d) => d.totals[k]).filter((v) => v != null);
      return [
        k,
        known.length ? round1(known.reduce((a, v) => a + v, 0)) : null,
      ];
    }),
  );
  const incomplete = Object.fromEntries(
    KEYS.map((k) => [k, days.some((d) => d.incomplete[k])]),
  );
  const display = state.goal?.numbers_display ?? "show";
  const hideEnergy = display !== "show";
  const hideMacros = display === "hide_all";
  const redact = (t) => ({
    ...t,
    energy_kcal: hideEnergy ? null : t.energy_kcal,
    sugars_g: hideMacros ? null : t.sugars_g,
    salt_g: hideMacros ? null : t.salt_g,
    protein_g: hideMacros ? null : t.protein_g,
  });
  return [
    200,
    {
      numbers_hidden: { energy: hideEnergy, macros: hideMacros },
      member_id: memberId,
      period: n === 7 ? "week" : "day",
      start: days[0].date,
      end,
      totals: redact(totals),
      incomplete,
      limits: WEEK.limits,
      bands: UNKNOWN_BANDS,
      days: days.map((d) => ({ ...d, totals: redact(d.totals) })),
      pending_clinician_review: true,
    },
  ];
}

// ---- Daily guide (e2e/guide.spec.ts) ----------------------------------------
// The stub never computes a target: it serves a golden TargetsOut chosen from
// what was posted (packages/test-fixtures/targets/expected). Hidden numbers
// are the golden hide_* files, as the API would redact them.

const targetsGolden = (stem) => read(`targets/expected/${stem}.json`);

function targetsStem(display, direction, bodyFat) {
  if (display === "hide_all") return "g1_hide_all";
  if (display === "hide_energy") return "g1_hide_energy";
  if (direction === "lose") return "g2_lose_adjusted";
  return bodyFat != null ? "g11_lean_mass" : "g1_build_muscle";
}

function targetsRoute(method, path, b) {
  const primary = state.members.find((m) => m.is_primary);
  const gated = !(
    (method === "PUT" && path === "/v1/targets/display") ||
    (method === "DELETE" && path === "/v1/targets/settings")
  );
  if (termsMissing())
    return [403, envelope("consent_required", { purposes: ["terms"] })];
  if (gated && state.consents.health_data === null)
    return [403, envelope("consent_required", { purposes: ["health_data"] })];
  const g = state.goal;
  const stemFor = () =>
    targetsStem(g?.numbers_display, g?.direction, primary.body_fat_pct);
  if (method === "GET" && path === "/v1/targets/settings") return [200, g];
  if (method === "GET" && path === "/v1/targets")
    return [200, targetsGolden(g ? stemFor() : "none")];
  if (method === "POST" && path === "/v1/targets/preview") {
    const fat =
      b.body && "body_fat_pct" in b.body
        ? b.body.body_fat_pct
        : primary.body_fat_pct;
    return [
      200,
      targetsGolden(targetsStem(b.numbers_display, b.direction, fat)),
    ];
  }
  if (method === "PUT" && path === "/v1/targets/settings") {
    state.goal = {
      summary_view: "remaining",
      numbers_display: "show",
      energy_mode: "formula",
      fat_pct_energy: null,
      rate_pct_bw_per_week: null,
      target_weight_kg: null,
      sex_reference: null,
      ...b,
      member_id: primary.id,
      updated_at: new Date().toISOString(),
    };
    return [
      200,
      targetsGolden(
        targetsStem(b.numbers_display, b.direction, primary.body_fat_pct),
      ),
    ];
  }
  if (method === "PUT" && path === "/v1/targets/display") {
    if (!g) return [404, envelope("goal_settings_not_found")];
    if (b.numbers_display) g.numbers_display = b.numbers_display;
    if (b.summary_view) g.summary_view = b.summary_view;
    g.updated_at = new Date().toISOString();
    // DisplayOut: no settings fields
    return [
      200,
      {
        member_id: g.member_id,
        numbers_display: g.numbers_display,
        summary_view: g.summary_view,
        updated_at: g.updated_at,
      },
    ];
  }
  if (method === "DELETE" && path === "/v1/targets/settings") {
    state.goal = null;
    return [204, undefined];
  }
  return [404, envelope("not_found")];
}

function route(method, path, b, q = new URLSearchParams()) {
  if (path.startsWith("/v1/targets")) return targetsRoute(method, path, b);
  if (method === "GET" && path === "/v1/me")
    return [
      200,
      {
        id: E2E_USER_ID,
        email: "e2e@example.test",
        display_name: null,
        language: "en",
        created_at: "2026-01-01T00:00:00Z",
        timezone: state.timezone,
      },
    ];
  if (method === "PUT" && path === "/v1/me/timezone") {
    state.timezone = b.timezone;
    return [
      200,
      {
        id: E2E_USER_ID,
        email: "e2e@example.test",
        display_name: null,
        language: "en",
        created_at: "2026-01-01T00:00:00Z",
        timezone: state.timezone,
      },
    ];
  }
  if (method === "DELETE" && path === "/v1/me") {
    if (state.deleteFails > 0) {
      state.deleteFails -= 1;
      return [503, envelope("deletion_incomplete")];
    }
    state.deleted = true;
    return [204, undefined];
  }
  if (method === "GET" && path === "/v1/me/user-types")
    return [200, userTypesOut()];
  if (method === "PUT" && path === "/v1/me/user-types") return putUserTypes(b);
  if (method === "PATCH" && path === "/v1/me/user-types/active")
    return setActive(b);
  if (method === "GET" && path === "/v1/consents")
    return [200, consentStates()];
  if (method === "POST" && path === "/v1/consents") {
    if (b.granted && b.version !== CONSENT_VERSION)
      return [422, envelope("consent_version_mismatch")];
    state.consents[b.purpose] = b.granted ? b.version : null;
    return [200, consentStates()];
  }
  if (method === "GET" && path === "/v1/members") return [200, state.members];
  if (method === "POST" && path === "/v1/members") {
    if (writesHealth(b) && state.consents.health_data === null)
      return [403, envelope("consent_required", { purpose: "health_data" })];
    state.seq += 1;
    const m = {
      sex: null,
      height_cm: null,
      weight_kg: null,
      body_fat_pct: null,
      diet: "non_veg",
      allergens: [],
      conditions: [],
      custom_alerts: [],
      goal: null,
      ...b,
      id: `b0000000-0000-4000-8000-${String(state.seq).padStart(12, "0")}`,
      is_primary: false,
    };
    state.members.push(m);
    return [201, m];
  }
  const one = path.match(/^\/v1\/members\/([0-9a-f-]{36})$/);
  if (one) {
    const m = state.members.find((x) => x.id === one[1]);
    if (!m) return [404, envelope("member_not_found")];
    if (method === "GET") return [200, m];
    if (method === "DELETE") {
      state.members = state.members.filter((x) => x !== m);
      return [204, undefined];
    }
    if (method === "PATCH") {
      // body_fat_pct null is "unchanged"; only the clear flag clears it (D3).
      const { clear_body_fat_pct: clear, body_fat_pct: fat, ...rest } = b;
      Object.assign(m, rest);
      if (clear) m.body_fat_pct = null;
      else if (fat != null) m.body_fat_pct = fat;
      return [200, m];
    }
  }
  if (method === "POST" && path === "/v1/scans/upload-url") {
    if (termsMissing())
      return [403, envelope("consent_required", { purposes: ["terms"] })];
    return [
      200,
      {
        upload_url: `http://127.0.0.1:${authPort}/storage/v1/object/upload/sign/label-photos/${E2E_USER_ID}/label.jpg?token=e2e`,
        path: `${E2E_USER_ID}/label.jpg`,
        expires_in: 7200,
      },
    ];
  }
  if (method === "POST" && path === "/v1/scans/label") {
    if (termsMissing())
      return [403, envelope("consent_required", { purposes: ["terms"] })];
    return [
      200,
      {
        scan_id: "0b6c1f8e-3c1a-4f0e-9a51-1d2e3f4a5b6c",
        cached: false,
        prompt_version: "label-extract-v3",
        draft: read("drafts/clean.json"),
      },
    ];
  }
  if (method === "POST" && path === "/v1/analyze") {
    if (termsMissing())
      return [403, envelope("consent_required", { purposes: ["terms"] })];
    state.scans += 1;
    return [200, analyze()];
  }
  // The meals routes share the terms gate (ruling G1).
  if (
    (path.startsWith("/v1/meals") ||
      path.startsWith("/v1/foods") ||
      path.startsWith("/v1/custom-foods") ||
      path.startsWith("/v1/favourites") ||
      path.startsWith("/v1/recipes") ||
      path.startsWith("/v1/diary") ||
      path.startsWith("/v1/meal-slots")) &&
    termsMissing()
  )
    return [403, envelope("consent_required", { purposes: ["terms"] })];
  if (method === "GET" && path === "/v1/meal-slots")
    return [
      200,
      {
        items:
          q.get("include_archived") === "true"
            ? [...state.slots]
                .sort((a, b) => a.position - b.position)
                .map(publicSlot)
            : slotRows().map(publicSlot),
        suggested_slot_id: suggestedSlot(),
      },
    ];
  if (path.startsWith("/v1/meal-slots/") || path === "/v1/meal-slots") {
    const slotRoute = mealSlotRoute(method, path, b);
    if (slotRoute) return slotRoute;
  }
  if (method === "GET" && path === "/v1/foods/search") {
    const needle = (q.get("q") ?? "").trim().toLowerCase();
    const items =
      needle.length < 2
        ? null
        : [
            ...state.customFoods
              .filter((f) => f.name.toLowerCase().includes(needle))
              .map((f) => mineHit("custom_food", f)),
            ...state.recipes
              .filter((f) => f.name.toLowerCase().includes(needle))
              .map((f) => mineHit("recipe", f)),
            ...Object.values(FOODS)
              .filter((f) => f.name.toLowerCase().includes(needle))
              .map(foodHit),
          ];
    if (items === null) return [422, envelope("search_query_too_short")];
    return [200, { items, partial: false, failed_sources: [] }];
  }
  const customRoute = customFoodRoutes(method, path, q, b);
  if (customRoute) return customRoute;
  const recipeRoute = recipeRoutes(method, path, q, b);
  if (recipeRoute) return recipeRoute;
  const foodGet = path.match(
    /^\/v1\/foods\/(food|product|off|custom_food|recipe)\/([0-9a-f-]{36})$/,
  );
  if (foodGet && method === "GET") {
    const f =
      mineFood(foodGet[1], foodGet[2]) ?? FOODS[`${foodGet[1]}:${foodGet[2]}`];
    if (!f) return [404, envelope("food_not_found")];
    const d = display();
    const hidden = { energy: d !== "show", macros: d === "hide_all" };
    return [
      200,
      {
        ...f,
        per_100: Object.fromEntries(
          Object.entries(f.per_100).map(([k, v]) => [
            k,
            (k === "energy_kcal" ? hidden.energy : hidden.macros) ? null : v,
          ]),
        ),
        numbers_hidden: hidden,
      },
    ];
  }
  if (method === "GET" && path === "/v1/diary/day")
    return diaryDayOut(q.get("date"));
  if (method === "GET" && path === "/v1/diary/week")
    return diaryWeekOut(q.get("end"));
  if (method === "GET" && path === "/v1/diary/recents") return diaryRecents();
  const status = path.match(/^\/v1\/diary\/days\/(\d{4}-\d{2}-\d{2})\/status$/);
  if (status && method === "PUT") {
    if (status[1] > istDate(nowIso())) return [422, envelope("date_in_future")];
    state.partial[status[1]] = Boolean(b.partial_logged);
    return [
      200,
      { date: status[1], partial_logged: Boolean(b.partial_logged) },
    ];
  }
  if (path.startsWith("/v1/favourites")) {
    const out = favouriteRoutes(method, path, b);
    if (out) return out;
  }
  if (method === "POST" && path === "/v1/meals/copy") return copyMeals(b);
  if (method === "POST" && path === "/v1/meals") return logMeal(b);
  if (method === "GET" && path === "/v1/meals") {
    const from = new Date(q.get("from")).getTime();
    const to = new Date(q.get("to")).getTime();
    const list = state.meals
      .filter((m) => m.member_id === q.get("member_id"))
      .filter((m) => {
        const t = new Date(m.eaten_at).getTime();
        return t >= from && t < to;
      })
      .sort((x, y) => y.eaten_at.localeCompare(x.eaten_at))
      .map(publicMeal);
    return [200, list];
  }
  if (method === "GET" && path === "/v1/meals/summary") return summary(q);
  if (method === "GET" && path === "/v1/meals/week_counts") {
    const end = q.get("date") ?? istDate(new Date().toISOString());
    return [
      200,
      {
        start: addDays(end, -6),
        end,
        scans: state.scans,
        logged: state.meals.length,
      },
    ];
  }
  const meal = path.match(/^\/v1\/meals\/([0-9a-f-]{36})$/);
  if (meal && method === "PATCH") return patchMeal(meal[1], b);
  if (meal && method === "DELETE") {
    const before = state.meals.length;
    state.meals = state.meals.filter((m) => m.id !== meal[1]);
    return state.meals.length < before
      ? [204, undefined]
      : [404, envelope("meal_not_found")];
  }
  return [404, envelope("not_found")];
}

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "authorization, content-type",
  "access-control-allow-methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
};

reset();

createServer((req, res) => {
  if (req.url === "/health") {
    res.writeHead(200).end("ok");
    return;
  }
  if (req.method === "OPTIONS") {
    res.writeHead(204, CORS).end();
    return;
  }
  if (req.method === "POST" && req.url?.startsWith("/__reset")) {
    reset(new URL(req.url, "http://x").searchParams);
    res.writeHead(204).end();
    return;
  }
  if (/^\/v1\/products\/.*\/alternatives(\?|$)/.test(req.url ?? "")) {
    // Canned: the stub never ranks products.
    res.writeHead(200, { ...CORS, "content-type": "application/json" });
    res.end(JSON.stringify({ items: [], reason: "no_category" }));
    return;
  }
  if (req.method === "GET" && req.url === "/__state") {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify(state));
    return;
  }
  if (req.method === "GET" && req.url?.startsWith("/v1/methodology")) {
    // Public: the golden response (language is echoed; the values are the same).
    const language =
      new URL(req.url, "http://x").searchParams.get("language") ?? "en";
    res.writeHead(200, { ...CORS, "content-type": "application/json" });
    res.end(
      JSON.stringify({ ...read("responses/methodology.json"), language }),
    );
    return;
  }
  if (req.url?.startsWith("/v1/products/")) {
    const ok = req.url.startsWith("/v1/products/8901063201089/public");
    res.writeHead(ok ? 200 : 404, { "content-type": "application/json" });
    res.end(JSON.stringify(ok ? body : envelope("product_not_found")));
    return;
  }
  let raw = "";
  req.on("data", (c) => {
    raw += c;
  });
  req.on("end", () => {
    const signedIn = req.headers.authorization?.startsWith("Bearer ");
    const [status, out] = signedIn
      ? route(
          req.method,
          new URL(req.url, "http://x").pathname,
          raw ? JSON.parse(raw) : {},
          new URL(req.url, "http://x").searchParams,
        )
      : [401, envelope("auth_required")];
    res.writeHead(status, { ...CORS, "content-type": "application/json" });
    res.end(out === undefined ? undefined : JSON.stringify(out));
  });
}).listen(port, "127.0.0.1");

// Supabase Auth stand-in: the e2e session uses an HS256 token, so
// getClaims() verifies it by calling GET /auth/v1/user.
// The signed upload URL's target (Supabase Storage): records whether the
// uploaded photo still carries metadata (EXIF, GPS, comments).
function inspectUpload(bytes) {
  const text = bytes.toString("latin1");
  return {
    size: bytes.length,
    jpeg: bytes[0] === 0xff && bytes[1] === 0xd8,
    exif: text.includes("Exif"),
    gps: text.includes("GPS"),
    comment: text.includes("shot at home"),
  };
}

const STORAGE_CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "content-type, x-upsert",
  "access-control-allow-methods": "PUT, OPTIONS",
};

createServer((req, res) => {
  if (req.url?.startsWith("/storage/v1/object/upload/sign/")) {
    if (req.method === "OPTIONS") {
      res.writeHead(204, STORAGE_CORS).end();
      return;
    }
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => {
      state.upload = inspectUpload(Buffer.concat(chunks));
      res.writeHead(200, {
        ...STORAGE_CORS,
        "content-type": "application/json",
      });
      res.end(JSON.stringify({ Key: "label-photos/label.jpg" }));
    });
    return;
  }
  if (req.method === "POST" && req.url?.startsWith("/auth/v1/logout")) {
    res.writeHead(204).end();
    return;
  }
  if (req.url === "/auth/v1/user" && req.headers.authorization) {
    res.writeHead(200, { "content-type": "application/json" });
    res.end(
      JSON.stringify({
        id: E2E_USER_ID,
        aud: "authenticated",
        role: "authenticated",
        email: "e2e@example.test",
        app_metadata: { provider: "email" },
        user_metadata: {},
        created_at: "2026-01-01T00:00:00Z",
      }),
    );
    return;
  }
  res.writeHead(404, { "content-type": "application/json" }).end("{}");
}).listen(authPort, "127.0.0.1");
