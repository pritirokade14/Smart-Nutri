import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const root = new URL("../", import.meta.url);
const tokens = JSON.parse(readFileSync(new URL("tokens.json", root), "utf8"));
const css = fileURLToPath(new URL("build/css/tokens.css", root));
const dart = fileURLToPath(new URL("build/dart/tokens.dart", root));

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
test("unknown is never green", () => {
  const [h, s] = hsl(tok("color.verdict.unknown"));
  assert.ok(s < 0.15 || h < 70 || h > 170);
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
  assert.match(s, /--space-4:\s*16px/);
});
test("dart output exposes SnTokens", () => {
  const s = readFileSync(dart, "utf8");
  assert.match(s, /abstract final class SnTokens/);
  assert.match(s, /static const Color verdictOk = Color\(0xFF15803D\)/);
  assert.match(s, /static const Color verdictUnknown = Color\(0xFF4B5563\)/);
});
