import test from "node:test";
import assert from "node:assert/strict";
import { checkKeys, loadAll, placeholders } from "./check-keys.mjs";

test("missing key reported", () =>
  assert.match(checkKeys({ en: { a: "x", b: "y" }, hi: { a: "x" } }).join(), /hi.*missing.*b/));
test("extra key reported", () =>
  assert.match(checkKeys({ en: { a: "x" }, hi: { a: "x", z: "y" } }).join(), /hi.*extra.*z/));
test("placeholder mismatch reported", () =>
  assert.match(checkKeys({ en: { w: "Hi {name}" }, mr: { w: "Hi {nom}" } }).join(), /mr.*w.*placeholder/));
test("plural placeholders are extracted from nested ICU", () =>
  assert.deepEqual(placeholders("{n, plural, one {# item of {kind}} other {# items}}"), ["kind", "n"]));
test("repo messages are consistent", () => assert.deepEqual(checkKeys(loadAll()), []));
