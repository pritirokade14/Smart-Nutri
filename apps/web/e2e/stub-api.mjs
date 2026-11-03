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
// POST /__reset?terms=current|old&delete_fails=N&user_types=unanswered|<a,b>
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
reset();

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

function logMeal(b) {
  const prior =
    b.client_id && state.meals.find((m) => m.client_id === b.client_id);
  if (prior) return [200, prior];
  if (!state.members.some((m) => m.id === b.member_id))
    return [404, envelope("member_not_found")];
  if (b.product_id !== SF.product_id)
    return [404, envelope("product_not_found")];
  const grams = b.grams ?? (b.servings ?? 0) * SF.serving_size_g;
  if (!(grams > 0)) return [422, envelope("portion_required")];
  const p = SF.per_100g;
  const snap = (v) => (v == null ? null : round1((v * grams) / 100));
  state.seq += 1;
  const meal = {
    id: `c0000000-0000-4000-8000-${String(state.seq).padStart(12, "0")}`,
    member_id: b.member_id,
    product_id: SF.product_id,
    barcode: null,
    product_name: SF.name,
    grade: "D",
    grams,
    eaten_at: b.eaten_at ?? new Date().toISOString(),
    nutrients: {
      energy_kcal: snap(p.energy_kcal),
      sugars_g: snap(p.sugars_g),
      salt_g: snap(p.salt_g),
      protein_g: snap(p.protein_g),
      fat_g: snap(p.fat_g),
      sat_fat_g: snap(p.sat_fat_g),
      carbs_g: snap(p.carbs_g),
    },
    client_id: b.client_id ?? null,
    attribution: null,
  };
  state.meals.push(meal);
  return [201, meal];
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
  return [
    200,
    {
      member_id: memberId,
      period: n === 7 ? "week" : "day",
      start: days[0].date,
      end,
      totals,
      incomplete,
      limits: WEEK.limits,
      bands: UNKNOWN_BANDS,
      days,
      pending_clinician_review: true,
    },
  ];
}

function route(method, path, b, q = new URLSearchParams()) {
  if (method === "GET" && path === "/v1/me")
    return [
      200,
      {
        id: E2E_USER_ID,
        email: "e2e@example.test",
        display_name: null,
        language: "en",
        created_at: "2026-01-01T00:00:00Z",
      },
    ];
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
      Object.assign(m, b);
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
  if (path.startsWith("/v1/meals") && termsMissing())
    return [403, envelope("consent_required", { purposes: ["terms"] })];
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
      .sort((x, y) => y.eaten_at.localeCompare(x.eaten_at));
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
