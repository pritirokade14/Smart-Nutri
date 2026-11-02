import test from "node:test";
import assert from "node:assert/strict";
import { argInfo, checkKeys, loadAll, parseIcu, placeholders } from "./check-keys.mjs";

test("missing key reported", () =>
  assert.match(checkKeys({ en: { a: "x", b: "y" }, hi: { a: "x" } }).join(), /hi.*missing.*b/));
test("extra key reported", () =>
  assert.match(checkKeys({ en: { a: "x" }, hi: { a: "x", z: "y" } }).join(), /hi.*extra.*z/));
test("placeholder mismatch reported", () =>
  assert.match(checkKeys({ en: { w: "Hi {name}" }, mr: { w: "Hi {nom}" } }).join(), /mr.*w.*placeholder/));
test("plural placeholders are extracted from nested ICU", () =>
  assert.deepEqual(placeholders("{n, plural, one {# item of {kind}} other {# items}}"), ["kind", "n"]));
test("argInfo records kinds and cases", () => {
  const info = argInfo("{b, select, per_serving {x} other {y}} {n}");
  assert.deepEqual([...info.get("b").kinds], ["select"]);
  assert.deepEqual([...info.get("b").cases].sort(), ["other", "per_serving"]);
  assert.deepEqual([...info.get("n").kinds], ["simple"]);
});
test("unbalanced braces are rejected", () => assert.throws(() => parseIcu("Hi {name")));

test("(a) select case set differing between locales is reported", () =>
  assert.match(
    checkKeys({
      en: { s: "{b, select, per_serving {a} other {b}}" },
      hi: { s: "{b, select, per_servng {a} other {b}}" },
    }).join(),
    /hi: key s \{b\} cases differ/,
  ));
test("(a) plural =N cases differing between locales is reported", () =>
  assert.match(
    checkKeys({
      en: { p: "{n, plural, =0 {none} one {#} other {#}}" },
      mr: { p: "{n, plural, one {#} other {#}}" },
    }).join(),
    /mr: key p \{n\} cases differ/,
  ));
test("(a) plural keyword categories may differ between locales", () =>
  assert.deepEqual(
    checkKeys({ en: { p: "{n, plural, one {#} other {#}}" }, hi: { p: "{n, plural, other {#}}" } }),
    [],
  ));
test("(b) select without other is reported, in en too", () => {
  const errs = checkKeys({
    en: { s: "{b, select, per_serving {a}}" },
    hi: { s: "{b, select, per_serving {a}}" },
  }).join("\n");
  assert.match(errs, /en: key s \{b\} has no other branch/);
  assert.match(errs, /hi: key s \{b\} has no other branch/);
});
test("(b) plural without other is reported", () =>
  assert.match(checkKeys({ en: { p: "{n, plural, one {#}}" } }).join(), /en: key p \{n\} has no other/));
test("(c) empty and whitespace-only translations are reported", () => {
  const errs = checkKeys({ en: { a: "x", b: "" }, hi: { a: "  ", b: "" } }).join("\n");
  assert.match(errs, /en: key b is empty/);
  assert.match(errs, /hi: key a is empty/);
});
test("(d) select in en but plain placeholder elsewhere is reported", () =>
  assert.match(
    checkKeys({ en: { s: "{b, select, x {a} other {b}}" }, mr: { s: "{b}" } }).join(),
    /mr: key s \{b\} is select in en but simple in mr/,
  ));
test("invalid ICU is reported", () =>
  assert.match(checkKeys({ en: { a: "x" }, hi: { a: "{oops" } }).join(), /hi: key a is not valid ICU/));
test("unknown plural keyword is reported", () =>
  assert.match(checkKeys({ en: { p: "{n, plural, oen {#} other {#}}" } }).join(), /unknown plural case "oen"/));
test("apostrophe before a brace is reported", () =>
  assert.match(checkKeys({ en: { a: "it'{x}" } }).join(), /apostrophe/));
test("repo messages are consistent", () => assert.deepEqual(checkKeys(loadAll()), []));
