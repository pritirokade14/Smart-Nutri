import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  deletePortion,
  type FoodDetailOut,
  type FoodKind,
  type FoodSearchOut,
  foodBarcodeKey,
  foodKey,
  foodSearchKey,
  getFood,
  getFoodByBarcode,
  putPortion,
  searchFoods,
} from "../api/foods";

const PERSONAL = { gcTime: 60_000, retry: false } as const;

export function useFoodSearch(
  q: string,
): UseQueryResult<FoodSearchOut, ApiError> {
  return useQuery<FoodSearchOut, ApiError>({
    queryKey: foodSearchKey(q),
    queryFn: () => searchFoods(q),
    enabled: q.length >= 2,
    ...PERSONAL,
  });
}

export function useFoodByBarcode(
  barcode: string | null,
): UseQueryResult<FoodDetailOut, ApiError> {
  return useQuery<FoodDetailOut, ApiError>({
    queryKey: foodBarcodeKey(barcode ?? ""),
    queryFn: () => getFoodByBarcode(barcode as string),
    enabled: barcode !== null,
    ...PERSONAL,
  });
}

export function useFood(
  kind: FoodKind,
  id: string,
): UseQueryResult<FoodDetailOut, ApiError> {
  return useQuery<FoodDetailOut, ApiError>({
    queryKey: foodKey(kind, id),
    queryFn: () => getFood(kind, id),
    ...PERSONAL,
  });
}

/** The PUT returns the food with the unit now resolving: no refetch needed. */
export function usePutPortion(
  kind: FoodKind,
  id: string,
): UseMutationResult<
  FoodDetailOut,
  ApiError,
  { unit: string; gramsPerUnit: number }
> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ unit, gramsPerUnit }) =>
      putPortion(kind, id, unit, gramsPerUnit),
    retry: false,
    onSuccess: (data) => client.setQueryData(foodKey(kind, id), data),
  });
}

export function useDeletePortion(
  kind: FoodKind,
  id: string,
): UseMutationResult<void, ApiError, string> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (unit: string) => deletePortion(kind, id, unit),
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: foodKey(kind, id) }),
  });
}
