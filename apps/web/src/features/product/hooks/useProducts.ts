import { type UseQueryResult, useQuery } from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  type AlternativesOut,
  type AlternativesSort,
  alternativesKey,
  type CompareOut,
  compareKey,
  compareProducts,
  getAlternatives,
  type ProductRef,
  SEARCH_MIN,
  type SearchHit,
  type SearchSort,
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
  sort: AlternativesSort = "grade",
): UseQueryResult<AlternativesOut, ApiError> {
  return useQuery<AlternativesOut, ApiError>({
    queryKey: ref
      ? alternativesKey(ref, memberId, sort)
      : ["alternatives", "none"],
    queryFn: () => getAlternatives(ref as ProductRef, memberId, sort),
    enabled: ref !== null,
    retry: retryOff,
    ...PERSONAL,
  });
}

export function useSearch(
  q: string,
  sort: SearchSort = "relevance",
  memberId: string | null = null,
): UseQueryResult<SearchHit[], ApiError> {
  const query = q.trim();
  const member = sort === "protein" ? memberId : null;
  return useQuery<SearchHit[], ApiError>({
    queryKey: searchKey(query, sort, member),
    queryFn: () => searchProducts(query, 20, sort, member),
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
