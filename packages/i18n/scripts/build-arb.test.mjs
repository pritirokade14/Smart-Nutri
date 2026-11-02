import test from "node:test";
import assert from "node:assert/strict";
import { flatten, buildArb } from "./build-arb.mjs";

test("flatten camelCases nested keys", () =>
  assert.deepEqual(flatten({ auth: { signIn: { google: "x" } } }), { authSignInGoogle: "x" }));
test("flatten camelCases snake_case segments", () =>
  assert.deepEqual(flatten({ reason: { sugar_high: "x" } }), { reasonSugarHigh: "x" }));
test("buildArb carries locale, sorted keys and placeholder metadata", () => {
  const arb = JSON.parse(buildArb("hi", { b: "x", a: "Hi {name}" }));
  assert.equal(arb["@@locale"], "hi");
  assert.deepEqual(Object.keys(arb), ["@@locale", "a", "@a", "b"]);
  assert.deepEqual(arb["@a"], { placeholders: { name: { type: "String" } } });
});
test("buildArb is deterministic", () =>
  assert.equal(buildArb("en", { b: "1", a: "2" }), buildArb("en", { a: "2", b: "1" })));
