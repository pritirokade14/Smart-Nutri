// Builds Flutter ARB files from messages/{en,hi,mr}.json.
// Nested keys flatten to camelCase (auth.signIn.google -> authSignInGoogle); output is deterministic.
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { argInfo } from "./check-keys.mjs";

export const LOCALES = ["en", "hi", "mr"];

const camel = (seg) => seg.replace(/[_-]+([a-zA-Z0-9])/g, (_, c) => c.toUpperCase());

export function flatten(obj, prefix = "") {
  const out = {};
  for (const [k, v] of Object.entries(obj)) {
    const seg = camel(k);
    const key = prefix ? prefix + seg[0].toUpperCase() + seg.slice(1) : seg;
    const entries = v !== null && typeof v === "object" ? flatten(v, key) : { [key]: v };
    for (const [ek, ev] of Object.entries(entries)) {
      if (ek in out) throw new Error(`flattened key collision: ${ek}`);
      out[ek] = ev;
    }
  }
  return out;
}

export function buildArb(locale, flat) {
  const arb = { "@@locale": locale };
  for (const key of Object.keys(flat).sort()) {
    arb[key] = flat[key];
    const info = argInfo(flat[key]);
    if (info.size) {
      // gen-l10n needs a numeric type for plural arguments; everything else is passed as a
      // pre-formatted String (numbers are formatted by the client for the locale).
      const type = (e) => (e.kinds.has("plural") || e.kinds.has("selectordinal") ? "num" : "String");
      arb["@" + key] = {
        placeholders: Object.fromEntries(
          [...info.keys()].sort().map((n) => [n, { type: type(info.get(n)) }]),
        ),
      };
    }
  }
  return JSON.stringify(arb, null, 2) + "\n";
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const here = dirname(fileURLToPath(import.meta.url));
  const outDir = join(here, "../../../apps/app/lib/core/l10n");
  mkdirSync(outDir, { recursive: true });
  for (const l of LOCALES) {
    const msgs = JSON.parse(readFileSync(join(here, `../messages/${l}.json`), "utf8"));
    const file = join(outDir, `app_${l}.arb`);
    writeFileSync(file, buildArb(l, flatten(msgs)));
    console.log("wrote", file);
  }
}
