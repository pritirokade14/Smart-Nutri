// Price per scoop (decision 6b, part 5): arithmetic on numbers the user
// typed, computed on this device only. The price is never stored, logged,
// sent to the API, put in a URL or a query key, or tracked. Cases:
// packages/test-fixtures/protein/price_per_scoop.json (shared with Android).

const ok = (n: number | null | undefined): n is number =>
  typeof n === "number" && Number.isFinite(n) && n > 0;

/**
 * `price x serving_size_g / pack_size_g`, rounded half up to 2 dp; null
 * when any input is missing or <= 0.
 */
export function pricePerScoop(
  price: number | null | undefined,
  packSizeG: number | null | undefined,
  servingSizeG: number | null | undefined,
): number | null {
  if (!ok(price) || !ok(packSizeG) || !ok(servingSizeG)) return null;
  const raw = (price * servingSizeG) / packSizeG;
  // Half up on the decimal value (avoids 1.005 * 100 = 100.49999...).
  return Math.round(Number(`${raw.toFixed(10)}e2`)) / 100;
}

/** A typed amount: a plain positive decimal, else null. */
export function parseAmount(raw: string): number | null {
  const s = raw.trim();
  if (!/^\d+(\.\d+)?$/.test(s)) return null;
  const n = Number(s);
  return n > 0 ? n : null;
}
