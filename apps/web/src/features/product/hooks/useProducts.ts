import { type UseQueryResult, useQuery } from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  type AlternativesOut,
  alternativesKey,
  type CompareOut,
  compareKey,
  compareProducts,
  getAlternatives,
  type ProductRef,
  SEARCH_MIN,
  type SearchHit,
  searchKey,
  searchProducts,
} from "../api/products";

// Member statuses are personal: not kept long once nobody is looking.
const PERSONAL = { gcTime: 60_000 } as const;

/** Retry an Open Food Facts outage (503) once; never a 4xx. */
const retryOff = (n: number, e: ApiError) => e.status === 503 && n < 1;

export function useAlternatives(
  ref: ProductRef | null,
  memberId: string | null,
): UseQueryResult<AlternativesOut, ApiError> {
  return useQuery<AlternativesOut, ApiError>({
    queryKey: ref ? alternativesKey(ref, memberId) : ["alternatives", "none"],
    queryFn: () => getAlternatives(ref as ProductRef, memberId),
    enabled: ref !== null,
    retry: retryOff,
    ...PERSONAL,
  });
}

export function useSearch(q: string): UseQueryResult<SearchHit[], ApiError> {
  const query = q.trim();
  return useQuery<SearchHit[], ApiError>({
    queryKey: searchKey(query),
    queryFn: () => searchProducts(query),
    enabled: query.length >= SEARCH_MIN,
    retry: retryOff,
    staleTime: 60_000,
    ...PERSONAL,
  });
}

export function useCompare(
  a: ProductRef,
  b: ProductRef | null,
  memberId: string | null,
): UseQueryResult<CompareOut, ApiError> {
  return useQuery<CompareOut, ApiError>({
    queryKey: b ? compareKey(a, b, memberId) : ["compare", "none"],
    queryFn: () => compareProducts(a, b as ProductRef, memberId),
    enabled: b !== null,
    retry: retryOff,
    ...PERSONAL,
  });
}
