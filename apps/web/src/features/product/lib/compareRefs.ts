import { normalizeBarcode } from "@/features/scan/lib/barcode";
import type { ProductRef } from "../api/products";

type Params = Record<string, string | string[] | undefined>;

// Same rule as normalizeProductId (kept here so the server page does not
// import the browser API client).
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const normalizeProductId = (id: string) =>
  UUID.test(id) ? id.toLowerCase() : null;

const one = (v: string | string[] | undefined) =>
  typeof v === "string" ? v : undefined;

/**
 * One side of /compare from its query parameters (the API's names: `a` or
 * `a_barcode`). Exactly one must be present and valid, else null.
 */
export function compareRef(
  params: Params,
  prefix: "a" | "b",
): ProductRef | null {
  const id = one(params[prefix]);
  const code = one(params[`${prefix}_barcode`]);
  if (id !== undefined && code !== undefined) return null;
  if (id !== undefined) {
    const productId = normalizeProductId(id);
    return productId ? { productId } : null;
  }
  if (code !== undefined) {
    const barcode = normalizeBarcode(code);
    return barcode ? { barcode } : null;
  }
  return null;
}

/** Whether the URL names a `prefix` side at all (valid or not). */
export function hasSide(params: Params, prefix: "a" | "b"): boolean {
  return (
    one(params[prefix]) !== undefined ||
    one(params[`${prefix}_barcode`]) !== undefined
  );
}
