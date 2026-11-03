import {
  type UseMutationResult,
  type UseQueryResult,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import type { ApiError } from "@/lib/api/errors";
import {
  dayMealsKey,
  deleteMeal,
  getSummary,
  getWeekCounts,
  listMealsForDay,
  logMeal,
  type MealIn,
  type MealOut,
  mealsKey,
  type Summary,
  type SummaryPeriod,
  summaryKey,
  type WeekCounts,
  weekCountsKey,
} from "../api/meals";

// Personal data: never kept long once nobody is looking at it.
const PERSONAL = { gcTime: 60_000, retry: false } as const;

/**
 * Log a meal. Never retried automatically: the dialog retries on the user's
 * tap with the same client_id, so a retry can never create a second row.
 */
export function useLogMeal(): UseMutationResult<MealOut, ApiError, MealIn> {
  const client = useQueryClient();
  return useMutation<MealOut, ApiError, MealIn>({
    mutationFn: logMeal,
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: mealsKey }),
  });
}

export function useDeleteMeal(): UseMutationResult<void, ApiError, string> {
  const client = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: deleteMeal,
    retry: false,
    onSuccess: () => client.invalidateQueries({ queryKey: mealsKey }),
  });
}

export function useMealsForDay(
  memberId: string | undefined,
  date: string,
): UseQueryResult<MealOut[], ApiError> {
  return useQuery<MealOut[], ApiError>({
    queryKey: dayMealsKey(memberId ?? "", date),
    queryFn: () => listMealsForDay(memberId as string, date),
    enabled: Boolean(memberId),
    ...PERSONAL,
  });
}

export function useSummary(
  memberId: string | undefined,
  period: SummaryPeriod,
  date: string,
): UseQueryResult<Summary, ApiError> {
  return useQuery<Summary, ApiError>({
    queryKey: summaryKey(memberId ?? "", period, date),
    queryFn: () => getSummary(memberId as string, period, date),
    enabled: Boolean(memberId),
    ...PERSONAL,
  });
}

export function useWeekCounts(
  date: string,
  enabled = true,
): UseQueryResult<WeekCounts, ApiError> {
  return useQuery<WeekCounts, ApiError>({
    queryKey: weekCountsKey(date),
    queryFn: () => getWeekCounts(date),
    enabled,
    ...PERSONAL,
  });
}
