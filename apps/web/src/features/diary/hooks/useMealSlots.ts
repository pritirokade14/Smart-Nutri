import { type UseQueryResult, useQuery } from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  listMealSlots,
  type MealSlotsOut,
  mealSlotsKey,
} from "../api/mealSlots";

export function useMealSlots(
  includeArchived = false,
): UseQueryResult<MealSlotsOut, ApiError> {
  return useQuery<MealSlotsOut, ApiError>({
    queryKey: mealSlotsKey(includeArchived),
    queryFn: () => listMealSlots(includeArchived),
    gcTime: 60_000,
    retry: false,
  });
}
