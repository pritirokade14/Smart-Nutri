// Checks messages/{en,hi,mr}.json:
//  - hi/mr have exactly the keys of en;
//  - every message is valid ICU, non-empty, and every select/plural has an `other` branch;
//  - hi/mr use the same ICU arguments as en, with the same kind (simple / select / plural)
//    and, for select, the same set of cases (plural `=N` cases must match too; plural
//    keyword categories such as one/few may legitimately differ between languages).
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const LOCALES = ["en", "hi", "mr"];
const BRANCHED = new Set(["select", "plural", "selectordinal"]);
const PLURAL_KEYWORDS = new Set(["zero", "one", "two", "few", "many", "other"]);

// Local flatten (dot paths) so this module has no dependency on build-arb.mjs.
function flat(obj, prefix = "") {
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (v !== null && typeof v === "object") Object.assign(out, flat(v, key));
    else out[key] = v;
  }
  return out;
}

// Minimal ICU MessageFormat parser (arguments, select/plural branches; `#` is plain text).
// Apostrophes are treated as literal text, as Flutter gen-l10n does by default.
// Returns a list of nodes: {type:"text", value} | {type:"arg", name, kind, cases?}.
export function parseIcu(msg) {
  const s = String(msg);
  let i = 0;
  const fail = (what) => {
    throw new Error(`${what} at position ${i}`);
  };
  const skipWs = () => {
    while (i < s.length && /\s/.test(s[i])) i++;
  };
  const readToken = () => {
    let out = "";
    while (i < s.length && s[i] !== "," && s[i] !== "}") {
      if (s[i] === "{") fail("unexpected {");
      out += s[i++];
    }
    if (i >= s.length) fail("unterminated argument");
    return out.trim();
  };
  const parseNodes = () => {
    const nodes = [];
    let text = "";
    while (i < s.length && s[i] !== "}") {
      if (s[i] === "{") {
        if (text) nodes.push({ type: "text", value: text });
        text = "";
        nodes.push(parseArg());
      } else text += s[i++];
    }
    if (text) nodes.push({ type: "text", value: text });
    return nodes;
  };
  const parseArg = () => {
    i++; // {
    const name = readToken();
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) fail(`bad argument name "${name}"`);
    if (s[i] === "}") {
      i++;
      return { type: "arg", name, kind: "simple" };
    }
    i++; // ,
    const kind = readToken();
    if (s[i] === "}") {
      i++;
      return { type: "arg", name, kind };
    }
    i++; // ,
    if (!BRANCHED.has(kind)) {
      readToken(); // style, e.g. {d, date, short}
      i++;
      return { type: "arg", name, kind };
    }
    const cases = {};
    for (;;) {
      skipWs();
      if (i >= s.length) fail(`unterminated ${kind}`);
      if (s[i] === "}") {
        i++;
        break;
      }
      let key = "";
      while (i < s.length && !/[\s{}]/.test(s[i])) key += s[i++];
      skipWs();
      if (key.startsWith("offset:")) continue;
      if (!key || s[i] !== "{") fail(`expected {…} after case "${key}"`);
      i++;
      const body = parseNodes();
      if (s[i] !== "}") fail(`unterminated case "${key}"`);
      i++;
      if (key in cases) fail(`duplicate case "${key}"`);
      cases[key] = body;
    }
    return { type: "arg", name, kind, cases };
  };
  const nodes = parseNodes();
  if (i < s.length) fail("unexpected }");
  return nodes;
}

// name -> {kinds: Set, cases: Set} for every argument, including nested ones.
export function argInfo(msg) {
  const info = new Map();
  const walk = (nodes) => {
    for (const n of nodes) {
      if (n.type !== "arg") continue;
      const e = info.get(n.name) ?? { kinds: new Set(), cases: new Set() };
      e.kinds.add(n.kind);
      for (const [key, body] of Object.entries(n.cases ?? {})) {
        e.cases.add(key);
        walk(body);
      }
      info.set(n.name, e);
    }
  };
  walk(parseIcu(msg));
  return info;
}

// Names of ICU arguments, including those nested inside plural/select branches.
export function placeholders(msg) {
  return [...argInfo(msg).keys()].sort();
}

const kindOf = (e) => [...e.kinds].sort().join("|");
const comparableCases = (e) =>
  [...e.cases].filter((c) => !e.kinds.has("plural") || c.startsWith("=")).sort().join(",");

// Problems in one message on its own (any locale, including en). Returns [errors, info|null].
function checkOne(loc, key, value) {
  if (typeof value !== "string" || value.trim() === "") return [[`${loc}: key ${key} is empty`], null];
  let info;
  try {
    info = argInfo(value);
  } catch (err) {
    return [[`${loc}: key ${key} is not valid ICU (${err.message})`], null];
  }
  const errors = [];
  if (/'[{}#|]/.test(value))
    errors.push(`${loc}: key ${key} has an apostrophe before a special character (quoting differs between clients)`);
  for (const [name, e] of info) {
    if (e.kinds.size > 1) errors.push(`${loc}: key ${key} uses {${name}} as ${kindOf(e)}`);
    if (![...e.kinds].some((k) => BRANCHED.has(k))) continue;
    if (!e.cases.has("other")) errors.push(`${loc}: key ${key} {${name}} has no other branch`);
    if (e.kinds.has("plural"))
      for (const c of e.cases)
        if (!PLURAL_KEYWORDS.has(c) && !/^=\d+$/.test(c))
          errors.push(`${loc}: key ${key} {${name}} has unknown plural case "${c}"`);
  }
  return [errors, info];
}

export function checkKeys(byLocale) {
  const errors = [];
  const base = flat(byLocale.en ?? {});
  const baseInfo = {};
  for (const [k, v] of Object.entries(base)) {
    const [errs, info] = checkOne("en", k, v);
    errors.push(...errs);
    baseInfo[k] = info;
  }
  for (const [loc, msgs] of Object.entries(byLocale)) {
    if (loc === "en") continue;
    const cur = flat(msgs);
    for (const k of Object.keys(base)) if (!(k in cur)) errors.push(`${loc}: missing key ${k}`);
    for (const k of Object.keys(cur)) if (!(k in base)) errors.push(`${loc}: extra key ${k}`);
    for (const k of Object.keys(base)) {
      if (!(k in cur)) continue;
      const [errs, info] = checkOne(loc, k, cur[k]);
      errors.push(...errs);
      const en = baseInfo[k];
      if (!info || !en) continue;
      const a = [...en.keys()].sort().join(",");
      const b = [...info.keys()].sort().join(",");
      if (a !== b) {
        errors.push(`${loc}: key ${k} placeholder mismatch (en {${a}} vs {${b}})`);
        continue;
      }
      for (const [name, e] of en) {
        const o = info.get(name);
        if (kindOf(e) !== kindOf(o)) {
          errors.push(`${loc}: key ${k} {${name}} is ${kindOf(e)} in en but ${kindOf(o)} in ${loc}`);
          continue;
        }
        const ca = comparableCases(e);
        const cb = comparableCases(o);
        if (ca !== cb) errors.push(`${loc}: key ${k} {${name}} cases differ (en [${ca}] vs [${cb}])`);
      }
    }
  }
  return errors;
}

export function loadAll() {
  const here = dirname(fileURLToPath(import.meta.url));
  return Object.fromEntries(
    LOCALES.map((l) => [l, JSON.parse(readFileSync(join(here, `../messages/${l}.json`), "utf8"))]),
  );
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const errors = checkKeys(loadAll());
  if (errors.length) {
    console.error(errors.join("\n"));
    process.exit(1);
  }
  console.log("i18n keys consistent");
}
