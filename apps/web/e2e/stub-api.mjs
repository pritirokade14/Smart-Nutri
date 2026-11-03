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
function reset() {
  state = {
    seq: 0,
    consents: Object.fromEntries(PURPOSES.map((p) => [p, null])),
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
  }));

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

function route(method, path, b) {
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
  if (method === "POST" && path === "/v1/analyze") return [200, analyze()];
  return [404, envelope("not_found")];
}

const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "authorization, content-type",
  "access-control-allow-methods": "GET, POST, PATCH, DELETE, OPTIONS",
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
  if (req.method === "POST" && req.url === "/__reset") {
    reset();
    res.writeHead(204).end();
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
        )
      : [401, envelope("auth_required")];
    res.writeHead(status, { ...CORS, "content-type": "application/json" });
    res.end(out === undefined ? undefined : JSON.stringify(out));
  });
}).listen(port, "127.0.0.1");

// Supabase Auth stand-in: the e2e session uses an HS256 token, so
// getClaims() verifies it by calling GET /auth/v1/user.
createServer((req, res) => {
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
