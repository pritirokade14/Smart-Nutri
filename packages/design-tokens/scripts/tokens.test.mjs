import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import StyleDictionary from "style-dictionary";
import { makeConfig, dartFormat } from "../style-dictionary.config.mjs";
import { fileURLToPath } from "node:url";

const root = new URL("../", import.meta.url);
const tokens = JSON.parse(readFileSync(new URL("tokens.json", root), "utf8"));
const css = fileURLToPath(new URL("build/css/tokens.css", root));
const dart = fileURLToPath(new URL("build/dart/tokens.dart", root));
const dartCopy = fileURLToPath(new URL("../../apps/app/lib/core/theme/tokens.g.dart", root));

const tok = (path) => path.split(".").reduce((o, k) => o[k], tokens).$value;
const lin = (c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const rgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
const lum = (hex) => { const [r, g, b] = rgb(hex).map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
const hsl = (hex) => {
  const [r, g, b] = rgb(hex);
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn, l = (mx + mn) / 2;
  if (d === 0) return [0, 0, l];
  const s = d / (1 - Math.abs(2 * l - 1));
  let h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4;
  h = (h * 60 + 360) % 360;
  return [h, s, l];
};

test("verdict colours meet WCAG AA on white", () => {
  for (const k of ["ok", "caution", "avoid", "unknown"])
    assert.ok(contrast(tok(`color.verdict.${k}`), "#FFFFFF") >= 4.5, k);
});
test("primary text meets AA on default surface", () => {
  assert.ok(contrast(tok("color.text.primary"), tok("color.surface.default")) >= 4.5);
});
// CIE76 colour distance (Lab) between two hex colours.
const lab = (hex) => {
  const [r, g, b] = rgb(hex).map(lin);
  const xyz = [
    (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047,
    0.2126 * r + 0.7152 * g + 0.0722 * b,
    (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883,
  ].map((t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116));
  return [116 * xyz[1] - 16, 500 * (xyz[0] - xyz[1]), 200 * (xyz[1] - xyz[2])];
};
const deltaE = (a, b) => Math.hypot(...lab(a).map((v, i) => v - lab(b)[i]));

// Hue 70-185 is green-ish (yellow-green through teal); there, only near-grey passes.
const isGreenish = (hex) => {
  const [h, s] = hsl(hex);
  return h >= 70 && h <= 185 && s >= 0.08;
};
const MIN_DELTA_E_FROM_OK = 25;
const unknownOk = (hex, ok = "#15803D") => !isGreenish(hex) && deltaE(hex, ok) >= MIN_DELTA_E_FROM_OK;

test("unknown is never green", () => {
  assert.ok(!isGreenish(tok("color.verdict.unknown")));
  assert.ok(deltaE(tok("color.verdict.unknown"), tok("color.verdict.ok")) >= MIN_DELTA_E_FROM_OK);
});
test("the green check rejects teal and grey-green candidates", () => {
  assert.ok(!unknownOk("#0F766E"));
  assert.ok(!unknownOk("#4B5B4B"));
  assert.ok(unknownOk("#4B5563"));
});
test("verdict values are pinned", () => {
  assert.equal(tok("color.verdict.ok"), "#15803D");
  assert.equal(tok("color.verdict.caution"), "#B45309");
  assert.equal(tok("color.verdict.avoid"), "#B91C1C");
  assert.equal(tok("color.verdict.unknown"), "#4B5563");
  assert.deepEqual(["a", "b", "c", "d", "e"].map((g) => tok(`color.grade.${g}`)),
    ["#038141", "#85BB2F", "#FECB02", "#EE8100", "#E63E11"]);
});
test("css output exposes verdict vars in a Tailwind @theme block", () => {
  const s = readFileSync(css, "utf8");
  assert.match(s, /@theme\s*\{/);
  assert.match(s, /--color-verdict-unknown:\s*#4B5563/i);
  assert.match(s, /--color-verdict-ok:\s*#15803D/i);
  assert.match(s, /--spacing-4:\s*16px/);
  assert.match(s, /--text-md:\s*16px/);
  assert.match(s, /--radius-lg:\s*16px/);
  assert.doesNotMatch(s, /--font-size-|--space-/);
});
test("dart output exposes SnTokens", () => {
  const s = readFileSync(dart, "utf8");
  assert.match(s, /abstract final class SnTokens/);
  assert.match(s, /static const Color verdictOk = Color\(0xFF15803D\)/);
  assert.match(s, /static const Color verdictUnknown = Color\(0xFF4B5563\)/);
});

// Light palette (color.*) and dark palette (color.dark.*) share the same
// semantic names; the web swaps them under prefers-color-scheme: dark.
const PALETTES = [
  ["light", "color"],
  ["dark", "color.dark"],
];
const VERDICTS = ["ok", "caution", "avoid", "unknown"];

for (const [mode, p] of PALETTES) {
  test(`${mode}: body and secondary text meet AA on every surface`, () => {
    for (const s of ["canvas", "default", "muted"])
      for (const tx of ["primary", "secondary"])
        assert.ok(contrast(tok(`${p}.text.${tx}`), tok(`${p}.surface.${s}`)) >= 4.5, `${tx} on ${s}`);
  });
  test(`${mode}: brand accent is readable (text on brand, brand as text)`, () => {
    for (const b of ["primary", "strong"])
      assert.ok(contrast(tok(`${p}.brand.on`), tok(`${p}.brand.${b}`)) >= 4.5, `on ${b}`);
    for (const s of ["canvas", "default"])
      assert.ok(contrast(tok(`${p}.brand.primary`), tok(`${p}.surface.${s}`)) >= 4.5, `brand on ${s}`);
    assert.ok(contrast(tok(`${p}.brand.primary`), tok(`${p}.brand.soft`)) >= 4.5, "brand on soft");
  });
  test(`${mode}: verdict colours are readable on their soft tint, the surface, and as badge fills`, () => {
    for (const v of VERDICTS) {
      const c = tok(`${p}.verdict.${v}`);
      assert.ok(contrast(c, tok(`${p}.verdict.soft.${v}`)) >= 4.5, `${v} on soft`);
      assert.ok(contrast(c, tok(`${p}.surface.default`)) >= 4.5, `${v} on surface`);
      assert.ok(contrast(tok(`${p}.text.inverse`), c) >= 4.5, `inverse on ${v}`);
    }
  });
  test(`${mode}: unknown is never green (solid and soft tint)`, () => {
    assert.ok(!isGreenish(tok(`${p}.verdict.unknown`)));
    assert.ok(!isGreenish(tok(`${p}.verdict.soft.unknown`)));
    assert.ok(deltaE(tok(`${p}.verdict.unknown`), tok(`${p}.verdict.ok`)) >= MIN_DELTA_E_FROM_OK);
  });
  test(`${mode}: the brand accent never reads as a verdict colour`, () => {
    const brand = tok(`${p}.brand.primary`);
    assert.ok(!isGreenish(brand), "brand is not green");
    for (const v of VERDICTS)
      assert.ok(deltaE(brand, tok(`${p}.verdict.${v}`)) >= MIN_DELTA_E_FROM_OK, `brand vs ${v}`);
  });
}
test("grade tiles carry a fixed on-colour (not swapped in dark mode)", () => {
  for (const g of ["a", "b", "c", "d", "e"])
    assert.ok(contrast(tok(`color.grade.on.${g}`), tok(`color.grade.${g}`)) >= 3, g); // large bold text
});
test("css output exposes the semantic and dark palette", () => {
  const s = readFileSync(css, "utf8");
  for (const v of [
    "--color-brand-primary",
    "--color-surface-canvas",
    "--color-text-secondary",
    "--color-verdict-soft-unknown",
    "--color-dark-surface-canvas",
    "--color-dark-verdict-unknown",
    "--color-grade-on-a",
    "--text-2xl",
    "--radius-xl",
  ])
    assert.match(s, new RegExp(`${v}:`), v);
});

test("committed outputs are fresh (rebuild is byte-identical)", async () => {
  const out = mkdtempSync(`${tmpdir()}/sn-tokens-`);
  try {
    const sd = new StyleDictionary(makeConfig(`${out}/`, fileURLToPath(new URL("tokens.json", root))), { verbosity: "silent" });
    await sd.buildAllPlatforms();
    const read = (p) => readFileSync(p, "utf8");
    assert.equal(read(`${out}/css/tokens.css`), read(css));
    assert.equal(read(`${out}/dart/tokens.dart`), read(dart));
    assert.equal(read(`${out}/dart/tokens.dart`), read(dartCopy));
  } finally {
    rmSync(out, { recursive: true, force: true });
  }
});
test("dart format rejects unexpected $type and malformed hex", () => {
  const run = (t) => dartFormat({ dictionary: { allTokens: [{ path: ["x"], ...t }] } });
  assert.throws(() => run({ $type: "shadow", $value: "1px" }), /unsupported \$type/);
  assert.throws(() => run({ $type: "color", $value: "#FFF" }), /6-digit hex/);
  assert.throws(() => run({ $type: "color", $value: "#12345678" }), /6-digit hex/);
  assert.throws(() => run({ $type: "dimension", $value: "1rem" }), /px dimension/);
});
