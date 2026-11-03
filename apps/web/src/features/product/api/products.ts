import type { components } from "@smartnutri/api-client";
import type { QueryClient } from "@tanstack/react-query";
import { call } from "@/lib/api/call";
import { getApi } from "@/lib/api/client";

export type AlternativesOut = components["schemas"]["AlternativesOut"];
export type AlternativeOut = components["schemas"]["AlternativeOut"];
export type SearchHit = components["schemas"]["SearchHit"];
export type CompareOut = components["schemas"]["CompareOut"];
export type CompareSide = components["schemas"]["CompareSide"];
export type BetterSide = components["schemas"]["BetterSide"];

/** A product reference: our own product id, or an Open Food Facts barcode. */
export type ProductRef = { productId: string } | { barcode: string };

export const refKey = (ref: ProductRef) =>
  "productId" in ref ? `id:${ref.productId}` : `bc:${ref.barcode}`;

// Query keys. Alternatives and compare carry a member's status: dropped on
// sign-out with the other personal data.
export const alternativesKey = (ref: ProductRef, memberId: string | null) =>
  ["alternatives", refKey(ref), memberId] as const;
export const searchKey = (q: string) => ["search", q] as const;
export const compareKey = (
  a: ProductRef,
  b: ProductRef,
  memberId: string | null,
) => ["compare", refKey(a), refKey(b), memberId] as const;

/** Up to 5 healthier options in the same category (API order kept). */
export function getAlternatives(
  ref: ProductRef,
  memberId: string | null,
): Promise<AlternativesOut> {
  const api = getApi();
  const query = memberId ? { member_id: memberId } : {};
  return "productId" in ref
    ? call(
        api.GET("/v1/products/{product_id}/alternatives", {
          params: { path: { product_id: ref.productId }, query },
        }),
      )
    : call(
        api.GET("/v1/products/barcode/{code}/alternatives", {
          params: { path: { code: ref.barcode }, query },
        }),
      );
}

export const SEARCH_MIN = 3;
export const SEARCH_MAX = 80;

export function searchProducts(q: string, limit = 20): Promise<SearchHit[]> {
  const api = getApi();
  return call(
    api.GET("/v1/products/search", { params: { query: { q, limit } } }),
  );
}

function side(prefix: "a" | "b", ref: ProductRef) {
  return "productId" in ref
    ? { [prefix]: ref.productId }
    : { [`${prefix}_barcode`]: ref.barcode };
}

export function compareProducts(
  a: ProductRef,
  b: ProductRef,
  memberId: string | null,
): Promise<CompareOut> {
  const api = getApi();
  return call(
    api.GET("/v1/products/compare", {
      params: {
        query: {
          ...side("a", a),
          ...side("b", b),
          ...(memberId ? { member_id: memberId } : {}),
        },
      },
    }),
  );
}

/** The logged-in page for a product: a barcode result, or a saved product. */
export function productHref(
  locale: string,
  p: { product_id: string | null; barcode: string | null },
): string | null {
  if (p.barcode) return `/${locale}/result/${encodeURIComponent(p.barcode)}`;
  if (p.product_id) return `/${locale}/product/${p.product_id}`;
  return null;
}

/** A side of /compare as query parameters (the API's own names). */
export function compareParams(
  prefix: "a" | "b",
  p: { product_id: string | null; barcode: string | null },
): Record<string, string> | null {
  if (p.product_id) return { [prefix]: p.product_id };
  if (p.barcode) return { [`${prefix}_barcode`]: p.barcode };
  return null;
}

export function compareHref(
  locale: string,
  a: Record<string, string>,
  b?: Record<string, string> | null,
): string {
  const q = new URLSearchParams({ ...a, ...(b ?? {}) });
  return `/${locale}/compare?${q.toString()}`;
}

/** Drops alternatives, compare and search results on sign-out. */
export function clearProductsCache(client: QueryClient): void {
  client.removeQueries({ queryKey: ["alternatives"] });
  client.removeQueries({ queryKey: ["compare"] });
  client.removeQueries({ queryKey: ["search"] });
}
