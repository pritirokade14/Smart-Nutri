// Checks hi/mr against en: same keys, same ICU placeholder names.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const LOCALES = ["en", "hi", "mr"];

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

// Names of ICU arguments, including those nested inside plural/select branches.
export function placeholders(msg) {
  const names = new Set();
  const walk = (s) => {
    let i = 0;
    while (i < s.length) {
      if (s[i] !== "{") {
        i++;
        continue;
      }
      let depth = 1;
      let j = i + 1;
      while (j < s.length && depth > 0) {
        if (s[j] === "{") depth++;
        else if (s[j] === "}") depth--;
        j++;
      }
      const body = s.slice(i + 1, j - 1);
      const comma = body.indexOf(",");
      names.add((comma < 0 ? body : body.slice(0, comma)).trim());
      if (comma >= 0) {
        // plural/select: recurse into each branch body (not the branch selector itself)
        const second = body.indexOf(",", comma + 1);
        if (second >= 0) {
          const rest = body.slice(second + 1);
          let k = 0;
          while (k < rest.length) {
            if (rest[k] !== "{") {
              k++;
              continue;
            }
            let d = 1;
            let m = k + 1;
            while (m < rest.length && d > 0) {
              if (rest[m] === "{") d++;
              else if (rest[m] === "}") d--;
              m++;
            }
            walk(rest.slice(k + 1, m - 1));
            k = m;
          }
        }
      }
      i = j;
    }
  };
  walk(String(msg));
  return [...names].sort();
}

export function checkKeys(byLocale) {
  const errors = [];
  const base = flat(byLocale.en ?? {});
  for (const [loc, msgs] of Object.entries(byLocale)) {
    if (loc === "en") continue;
    const cur = flat(msgs);
    for (const k of Object.keys(base)) if (!(k in cur)) errors.push(`${loc}: missing key ${k}`);
    for (const k of Object.keys(cur)) if (!(k in base)) errors.push(`${loc}: extra key ${k}`);
    for (const k of Object.keys(base)) {
      if (!(k in cur)) continue;
      const a = placeholders(base[k]).join(",");
      const b = placeholders(cur[k]).join(",");
      if (a !== b) errors.push(`${loc}: key ${k} placeholder mismatch (en {${a}} vs {${b}})`);
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
